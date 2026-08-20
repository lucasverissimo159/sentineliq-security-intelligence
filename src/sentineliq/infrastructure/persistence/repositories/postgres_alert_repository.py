"""PostgreSQL implementation of AlertRepositoryPort."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.value_objects.severity import Severity
from sentineliq.infrastructure.persistence.models import ThreatAlertModel


class PostgresAlertRepository(AlertRepositoryPort):
    """Fulfills AlertRepositoryPort using SQLAlchemy against PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_many(self, alerts: list[ThreatAlert]) -> None:
        self._session.add_all(_to_model(alert) for alert in alerts)
        await self._session.flush()

    async def find_by_id(self, alert_id: UUID) -> ThreatAlert | None:
        model = await self._session.get(ThreatAlertModel, alert_id)
        return _to_entity(model) if model else None

    async def list_unacknowledged(self, limit: int = 100) -> list[ThreatAlert]:
        stmt = (
            select(ThreatAlertModel)
            .where(ThreatAlertModel.acknowledged.is_(False))
            .order_by(ThreatAlertModel.detected_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(model) for model in result.scalars().all()]


def _to_model(alert: ThreatAlert) -> ThreatAlertModel:
    return ThreatAlertModel(
        id=alert.id,
        title=alert.title,
        explanation=alert.explanation,
        severity=int(alert.severity),
        related_log_ids=[str(log_id) for log_id in alert.related_log_ids],
        detected_at=alert.detected_at,
        acknowledged=alert.acknowledged,
    )


def _to_entity(model: ThreatAlertModel) -> ThreatAlert:
    from uuid import UUID as UUIDType

    return ThreatAlert(
        id=model.id,
        title=model.title,
        explanation=model.explanation,
        severity=Severity(model.severity),
        related_log_ids=[UUIDType(log_id) for log_id in (model.related_log_ids or [])],
        detected_at=model.detected_at,
        acknowledged=model.acknowledged,
    )
