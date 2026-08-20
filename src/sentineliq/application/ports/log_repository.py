"""Persistence boundary for LogEntry objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from sentineliq.domain.entities.log_entry import LogEntry


class LogRepositoryPort(ABC):
    """Contract any log storage technology must satisfy.

    The application layer depends only on this abstraction. Today it
    is fulfilled by `infrastructure.persistence.repositories
    .postgres_log_repository.PostgresLogRepository`; swapping to a
    different store later means writing a new adapter, not touching
    use cases.
    """

    @abstractmethod
    async def save_many(self, log_entries: list[LogEntry]) -> None:
        """Persist a batch of log entries."""

    @abstractmethod
    async def find_by_id(self, log_id: UUID) -> LogEntry | None:
        """Fetch a single log entry by id, or None if it doesn't exist."""

    @abstractmethod
    async def find_since(self, since: datetime, limit: int = 500) -> list[LogEntry]:
        """Fetch the most recent log entries occurring at or after `since`."""
