"""Severity value object shared across the domain."""
from __future__ import annotations

from enum import IntEnum


class Severity(IntEnum):
    """Ordered severity level for a log entry or threat alert.

    IntEnum is used deliberately so severities can be compared and
    sorted (e.g. `Severity.HIGH > Severity.LOW`) without extra logic.
    """

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_string(cls, value: str) -> Severity:
        try:
            return cls[value.strip().upper()]
        except KeyError as exc:
            raise ValueError(f"Unknown severity: {value!r}") from exc
