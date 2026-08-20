"""AI analysis boundary — fulfilled today by the Claude (Anthropic) adapter."""
from __future__ import annotations

from abc import ABC, abstractmethod

from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.entities.threat_alert import ThreatAlert


class AIAnalysisPort(ABC):
    """Contract for natural-language analysis of log data.

    The application layer asks this port for anomalies and summaries
    without knowing which model or vendor is behind it. This makes it
    possible to unit-test use cases with a fake implementation (see
    `tests/unit`) instead of making real, costly API calls.
    """

    @abstractmethod
    async def detect_anomalies(self, logs: list[LogEntry]) -> list[ThreatAlert]:
        """Analyze a window of logs and return any threat alerts found."""

    @abstractmethod
    async def summarize(
        self,
        logs: list[LogEntry],
        alerts: list[ThreatAlert],
    ) -> str:
        """Produce a human-readable incident summary for a window of activity."""
