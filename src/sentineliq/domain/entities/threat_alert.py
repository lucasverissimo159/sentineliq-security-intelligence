"""ThreatAlert: an anomaly or suspicious pattern identified across log entries."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sentineliq.domain.value_objects.severity import Severity


@dataclass(frozen=True, slots=True)
class ThreatAlert:
    """A finding produced by analysis (currently: the Claude adapter).

    `related_log_ids` keeps a traceable link back to the evidence that
    produced the alert, so a human reviewer (or a future automated
    responder) can always answer "why was this raised?".
    """

    id: UUID
    title: str
    explanation: str
    severity: Severity
    related_log_ids: list[UUID]
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged: bool = False

    @classmethod
    def new(
        cls,
        title: str,
        explanation: str,
        severity: Severity,
        related_log_ids: list[UUID],
    ) -> ThreatAlert:
        return cls(
            id=uuid4(),
            title=title,
            explanation=explanation,
            severity=severity,
            related_log_ids=related_log_ids,
        )

    def acknowledge(self) -> ThreatAlert:
        """Return a new, acknowledged copy of this alert (entities are immutable)."""
        return replace(self, acknowledged=True)
