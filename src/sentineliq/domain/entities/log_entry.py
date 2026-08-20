"""LogEntry: the core unit of data flowing through SentinelIQ."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sentineliq.domain.value_objects.severity import Severity


@dataclass(frozen=True, slots=True)
class LogEntry:
    """A single normalized log record coming from a monitored source.

    This is a pure domain object: it has no knowledge of *how* it is
    persisted (PostgreSQL), archived (S3), or analyzed (Claude). Those
    concerns live behind ports in `sentineliq.application.ports` and
    are fulfilled by adapters in `sentineliq.infrastructure`.
    """

    id: UUID
    source: str
    raw_message: str
    severity: Severity
    occurred_at: datetime
    ingested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        source: str,
        raw_message: str,
        severity: Severity,
        occurred_at: datetime,
        metadata: dict[str, str] | None = None,
    ) -> LogEntry:
        """Factory that assigns a fresh identity to a newly ingested log line."""
        return cls(
            id=uuid4(),
            source=source,
            raw_message=raw_message,
            severity=severity,
            occurred_at=occurred_at,
            metadata=metadata or {},
        )
