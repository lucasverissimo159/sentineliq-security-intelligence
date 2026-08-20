"""Use case: generate a natural-language incident report for a time window."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.domain.entities.analysis_report import AnalysisReport


@dataclass(slots=True)
class GenerateThreatReportUseCase:
    """Compose a human-readable summary of activity across a time window.

    This is the use case behind a "give me a plain-English summary of
    what happened last night" endpoint — the kind of feature that
    demonstrates real, practical value from the Claude integration
    rather than analysis living only in a black box.
    """

    log_repository: LogRepositoryPort
    alert_repository: AlertRepositoryPort
    ai_analysis: AIAnalysisPort

    async def execute(self, period_start: datetime, period_end: datetime) -> AnalysisReport:
        logs = await self.log_repository.find_since(period_start, limit=2000)
        logs = [log for log in logs if log.occurred_at <= period_end]

        alerts = await self.alert_repository.list_unacknowledged(limit=200)
        alerts = [a for a in alerts if period_start <= a.detected_at <= period_end]

        summary = await self.ai_analysis.summarize(logs, alerts)

        return AnalysisReport.new(
            summary=summary,
            period_start=period_start,
            period_end=period_end,
            alert_ids=[alert.id for alert in alerts],
        )
