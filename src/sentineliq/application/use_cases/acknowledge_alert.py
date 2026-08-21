"""Use case for acknowledging a threat alert."""
from __future__ import annotations

from uuid import UUID

from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.domain.exceptions import ThreatAlertNotFoundError


class AcknowledgeAlertUseCase:
    """Marks a threat alert as acknowledged by an operator."""

    def __init__(self, alert_repository: AlertRepositoryPort) -> None:
        self._alert_repository = alert_repository

    async def execute(self, alert_id: UUID) -> None:
        alert = await self._alert_repository.find_by_id(alert_id)
        if alert is None:
            raise ThreatAlertNotFoundError(alert_id)

        acknowledged_alert = alert.acknowledge()
        await self._alert_repository.update(acknowledged_alert)
