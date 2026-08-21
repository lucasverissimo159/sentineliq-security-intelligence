"""Persistence boundary for ThreatAlert objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sentineliq.domain.entities.threat_alert import ThreatAlert


class AlertRepositoryPort(ABC):
    """Contract any alert storage technology must satisfy."""

    @abstractmethod
    async def save_many(self, alerts: list[ThreatAlert]) -> None:
        """Persist a batch of newly detected alerts."""

    @abstractmethod
    async def find_by_id(self, alert_id: UUID) -> ThreatAlert | None:
        """Fetch a single alert by id, or None if it doesn't exist."""

    @abstractmethod
    async def list_unacknowledged(self, limit: int = 100) -> list[ThreatAlert]:
        """List alerts that have not yet been acknowledged by an operator."""

    @abstractmethod
    async def update(self, alert: ThreatAlert) -> None:
        """Update an existing alert."""
