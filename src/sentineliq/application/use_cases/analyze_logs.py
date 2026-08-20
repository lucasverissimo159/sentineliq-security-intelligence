"""Use case: analyze recent logs for anomalies using the AI analysis port."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.domain.entities.threat_alert import ThreatAlert


@dataclass(slots=True)
class AnalyzeLogsUseCase:
    """Pull a recent window of logs, ask the AI port for anomalies, persist findings.

    `window_minutes` controls how far back to look. In production this
    is expected to run on a schedule (e.g. every 5-15 minutes) — the
    scheduling mechanism itself (cron, APScheduler, an AWS Lambda on a
    EventBridge rule, ...) is an infrastructure decision left open for
    Jules AI to implement; see docs/ROADMAP.md.
    """

    log_repository: LogRepositoryPort
    alert_repository: AlertRepositoryPort
    ai_analysis: AIAnalysisPort
    window_minutes: int = 15

    async def execute(self) -> list[ThreatAlert]:
        since = datetime.now(UTC) - timedelta(minutes=self.window_minutes)
        recent_logs = await self.log_repository.find_since(since)

        if not recent_logs:
            return []

        alerts = await self.ai_analysis.detect_anomalies(recent_logs)

        if alerts:
            await self.alert_repository.save_many(alerts)

        return alerts
