"""Use case: generate a natural-language incident report for a time window."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.application.ports.object_storage import ObjectStoragePort
from sentineliq.application.ports.report_repository import ReportRepositoryPort
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
    report_repository: ReportRepositoryPort
    ai_analysis: AIAnalysisPort
    object_storage: ObjectStoragePort

    async def execute(self, period_start: datetime, period_end: datetime) -> AnalysisReport:
        logs = await self.log_repository.find_since(period_start, limit=2000)
        logs = [log for log in logs if log.occurred_at <= period_end]

        alerts = await self.alert_repository.list_unacknowledged(limit=200)
        alerts = [a for a in alerts if period_start <= a.detected_at <= period_end]

        summary = await self.ai_analysis.summarize(logs, alerts)

        report = AnalysisReport.new(
            summary=summary,
            period_start=period_start,
            period_end=period_end,
            alert_ids=[alert.id for alert in alerts],
        )

        timestamp = datetime.now(UTC).strftime("%Y/%m/%d/%H%M%S")
        key = f"reports/{timestamp}-{report.id}.json"

        payload = json.dumps(
            {
                "id": str(report.id),
                "summary": report.summary,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "alert_ids": [str(alert_id) for alert_id in report.alert_ids],
                "generated_at": report.generated_at.isoformat(),
            }
        ).encode("utf-8")

        await self.object_storage.upload(key, payload)

        # Entities are frozen, so we use object.__setattr__ to update the key
        object.__setattr__(report, 's3_object_key', key)

        await self.report_repository.save(report)
        return report
