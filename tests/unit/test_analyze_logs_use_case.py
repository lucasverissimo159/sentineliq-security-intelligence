"""Unit tests for AnalyzeLogsUseCase using fake ports."""
from __future__ import annotations

from sentineliq.application.use_cases.analyze_logs import AnalyzeLogsUseCase
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.value_objects.severity import Severity


async def test_analyze_logs_saves_alerts_found_by_ai_port(
    fake_log_repository, fake_alert_repository, fake_ai_analysis, sample_log_entry
):
    fake_log_repository.saved.append(sample_log_entry)
    fake_ai_analysis.anomalies_to_return = [
        ThreatAlert.new(
            title="Repeated blocked connections",
            explanation="Multiple blocked attempts from the same source in a short window.",
            severity=Severity.HIGH,
            related_log_ids=[sample_log_entry.id],
        )
    ]

    use_case = AnalyzeLogsUseCase(
        log_repository=fake_log_repository,
        alert_repository=fake_alert_repository,
        ai_analysis=fake_ai_analysis,
    )

    alerts = await use_case.execute()

    assert len(alerts) == 1
    assert fake_alert_repository.saved == alerts


async def test_analyze_logs_skips_ai_call_when_no_recent_logs(
    fake_log_repository, fake_alert_repository, fake_ai_analysis
):
    use_case = AnalyzeLogsUseCase(
        log_repository=fake_log_repository,
        alert_repository=fake_alert_repository,
        ai_analysis=fake_ai_analysis,
    )

    alerts = await use_case.execute()

    assert alerts == []
    assert fake_alert_repository.saved == []
