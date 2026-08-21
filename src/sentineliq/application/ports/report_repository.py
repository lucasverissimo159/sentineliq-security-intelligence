"""Persistence boundary for AnalysisReport objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sentineliq.domain.entities.analysis_report import AnalysisReport


class ReportRepositoryPort(ABC):
    """Contract any report storage technology must satisfy."""

    @abstractmethod
    async def save(self, report: AnalysisReport) -> None:
        """Persist a new analysis report."""

    @abstractmethod
    async def find_by_id(self, report_id: UUID) -> AnalysisReport | None:
        """Fetch a single report by id, or None if it doesn't exist."""
