"""PostgreSQL implementation of LogRepositoryPort."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.value_objects.severity import Severity
from sentineliq.infrastructure.persistence.models import LogEntryModel


class PostgresLogRepository(LogRepositoryPort):
    """Fulfills LogRepositoryPort using SQLAlchemy against PostgreSQL.

    A fresh `AsyncSession` is injected per request/use-case invocation
    (see `interfaces.api.dependencies`) rather than held here, which
    keeps this class stateless and safe to reuse.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_many(self, log_entries: list[LogEntry]) -> None:
        self._session.add_all(_to_model(entry) for entry in log_entries)
        await self._session.flush()

    async def find_by_id(self, log_id: UUID) -> LogEntry | None:
        model = await self._session.get(LogEntryModel, log_id)
        return _to_entity(model) if model else None

    async def find_since(self, since: datetime, limit: int = 500) -> list[LogEntry]:
        stmt = (
            select(LogEntryModel)
            .where(LogEntryModel.occurred_at >= since)
            .order_by(LogEntryModel.occurred_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(model) for model in result.scalars().all()]


def _to_model(entry: LogEntry) -> LogEntryModel:
    return LogEntryModel(
        id=entry.id,
        source=entry.source,
        raw_message=entry.raw_message,
        severity=int(entry.severity),
        occurred_at=entry.occurred_at,
        ingested_at=entry.ingested_at,
        log_metadata=entry.metadata,
    )


def _to_entity(model: LogEntryModel) -> LogEntry:
    return LogEntry(
        id=model.id,
        source=model.source,
        raw_message=model.raw_message,
        severity=Severity(model.severity),
        occurred_at=model.occurred_at,
        ingested_at=model.ingested_at,
        metadata=model.log_metadata or {},
    )
