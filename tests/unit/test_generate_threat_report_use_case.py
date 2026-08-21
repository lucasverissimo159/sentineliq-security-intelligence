"""Unit tests for the GenerateThreatReportUseCase."""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from sentineliq.application.use_cases.generate_threat_report import GenerateThreatReportUseCase
from tests.conftest import (
    FakeAIAnalysis,
    FakeAlertRepository,
    FakeLogRepository,
    FakeObjectStorage,
    FakeReportRepository,
)


@pytest.fixture
def use_case(
    fake_log_repository: FakeLogRepository,
    fake_alert_repository: FakeAlertRepository,
    fake_report_repository: FakeReportRepository,
    fake_ai_analysis: FakeAIAnalysis,
    fake_object_storage: FakeObjectStorage,
) -> GenerateThreatReportUseCase:
    return GenerateThreatReportUseCase(
        log_repository=fake_log_repository,
        alert_repository=fake_alert_repository,
        report_repository=fake_report_repository,
        ai_analysis=fake_ai_analysis,
        object_storage=fake_object_storage,
    )


@pytest.mark.asyncio
async def test_generate_threat_report(
    use_case: GenerateThreatReportUseCase,
    fake_report_repository: FakeReportRepository,
    fake_object_storage: FakeObjectStorage,
    fake_ai_analysis: FakeAIAnalysis,
):
    period_start = datetime(2023, 1, 1, tzinfo=UTC)
    period_end = datetime(2023, 1, 2, tzinfo=UTC)

    fake_ai_analysis.summary_to_return = "A bad thing happened."

    report = await use_case.execute(period_start=period_start, period_end=period_end)

    # 1. Returned report is correct
    assert report.summary == "A bad thing happened."
    assert report.period_start == period_start
    assert report.period_end == period_end
    assert report.s3_object_key is not None

    # 2. Saved to repository
    saved_report = await fake_report_repository.find_by_id(report.id)
    assert saved_report is not None
    assert saved_report.id == report.id
    assert saved_report.s3_object_key == report.s3_object_key

    # 3. Uploaded to S3 properly
    assert len(fake_object_storage.objects) == 1
    uploaded_data = list(fake_object_storage.objects.values())[0]
    parsed_payload = json.loads(uploaded_data.decode("utf-8"))

    assert parsed_payload["id"] == str(report.id)
    assert parsed_payload["summary"] == "A bad thing happened."
