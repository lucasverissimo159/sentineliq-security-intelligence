"""Unit tests for acknowledging alerts."""
from __future__ import annotations

import uuid

import pytest

from sentineliq.application.use_cases.acknowledge_alert import AcknowledgeAlertUseCase
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.exceptions import ThreatAlertNotFoundError
from sentineliq.domain.value_objects.severity import Severity
from tests.conftest import FakeAlertRepository


@pytest.fixture
def use_case(fake_alert_repository: FakeAlertRepository) -> AcknowledgeAlertUseCase:
    return AcknowledgeAlertUseCase(alert_repository=fake_alert_repository)


@pytest.mark.asyncio
async def test_acknowledge_existing_alert(
    use_case: AcknowledgeAlertUseCase, fake_alert_repository: FakeAlertRepository
):
    alert_id = uuid.uuid4()
    alert = ThreatAlert(
        id=alert_id,
        title="Test Alert",
        explanation="Test Explanation",
        severity=Severity.HIGH,
        related_log_ids=[],
        detected_at=uuid.uuid1().time, # just some non-null dummy
        acknowledged=False,
    )
    await fake_alert_repository.save_many([alert])

    assert not alert.acknowledged

    await use_case.execute(alert_id)

    saved_alert = await fake_alert_repository.find_by_id(alert_id)
    assert saved_alert.acknowledged is True


@pytest.mark.asyncio
async def test_acknowledge_nonexistent_alert(use_case: AcknowledgeAlertUseCase):
    with pytest.raises(ThreatAlertNotFoundError):
        await use_case.execute(uuid.uuid4())
