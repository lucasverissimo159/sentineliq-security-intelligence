"""Claude (Anthropic) implementation of AIAnalysisPort."""
from __future__ import annotations

import json

from anthropic import AsyncAnthropic

from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.value_objects.severity import Severity
from sentineliq.infrastructure.config.settings import Settings

_ANOMALY_SYSTEM_PROMPT = """\
You are a security analyst reviewing normalized system/network log entries.
Identify genuine anomalies or suspicious patterns only — ignore routine, \
expected activity. Respond ONLY with a JSON array (no prose, no markdown \
fences). Each element must have this exact shape:
{"title": str, "explanation": str, "severity": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", \
"related_log_indexes": [int, ...]}
`related_log_indexes` refers to the 0-based position of the relevant entries \
in the numbered list you are given. If nothing is suspicious, return [].
"""

_SUMMARY_SYSTEM_PROMPT = """\
You are a security analyst writing a concise incident summary for a \
non-technical stakeholder. Given a window of log activity and any alerts \
already raised, write a short plain-English summary (3-6 sentences): what \
happened, what stands out, and whether anything needs attention. No markdown, \
no bullet points — plain prose.
"""


class ClaudeAnalysisAdapter(AIAnalysisPort):
    """Fulfills AIAnalysisPort using the Anthropic Messages API.

    Prompt construction is deliberately explicit and inspectable here
    rather than hidden behind a prompt-templating library — for a
    security tool, being able to see exactly what was sent to the
    model matters both for debugging and for trust.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def detect_anomalies(self, logs: list[LogEntry]) -> list[ThreatAlert]:
        if not logs:
            return []

        numbered_logs = "\n".join(
            f"{i}. [{log.severity.name}] source={log.source} "
            f"occurred_at={log.occurred_at.isoformat()} message={log.raw_message}"
            for i, log in enumerate(logs)
        )

        response = await self._client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=2048,
            system=_ANOMALY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": numbered_logs}],
        )

        findings = _parse_json_array(_extract_text(response))
        alerts: list[ThreatAlert] = []
        for finding in findings:
            indexes = finding.get("related_log_indexes", [])
            related_log_ids = [logs[i].id for i in indexes if 0 <= i < len(logs)]
            alerts.append(
                ThreatAlert.new(
                    title=finding["title"],
                    explanation=finding["explanation"],
                    severity=Severity.from_string(finding["severity"]),
                    related_log_ids=related_log_ids,
                )
            )
        return alerts

    async def summarize(self, logs: list[LogEntry], alerts: list[ThreatAlert]) -> str:
        if not logs and not alerts:
            return "No activity was recorded in the selected period."

        log_lines = "\n".join(
            f"- [{log.severity.name}] {log.source}: {log.raw_message}" for log in logs[:200]
        )
        alert_lines = "\n".join(
            f"- ({alert.severity.name}) {alert.title}: {alert.explanation}" for alert in alerts
        )
        user_content = (
            f"Log activity ({len(logs)} entries, showing up to 200):\n{log_lines}\n\n"
            f"Alerts raised ({len(alerts)}):\n{alert_lines or 'None'}"
        )

        response = await self._client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=1024,
            system=_SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return _extract_text(response)


def _extract_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text").strip()


def _parse_json_array(text: str) -> list[dict]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        # Defensive fallback: the model is instructed to return raw JSON,
        # but if it wraps the array in prose/fences, extract the first
        # top-level [...] block before giving up.
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return []
