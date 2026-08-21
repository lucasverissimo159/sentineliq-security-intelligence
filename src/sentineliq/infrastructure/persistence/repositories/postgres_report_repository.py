"""PostgreSQL implementation of ReportRepositoryPort."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sentineliq.application.ports.report_repository import ReportRepositoryPort
from sentineliq.domain.entities.analysis_report import AnalysisReport
from sentineliq.infrastructure.persistence.models import AnalysisReportModel


class PostgresReportRepository(ReportRepositoryPort):
    """Fulfills ReportRepositoryPort using SQLAlchemy against PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: AnalysisReport) -> None:
        self._session.add(_to_model(report))
        await self._session.flush()

    async def find_by_id(self, report_id: UUID) -> AnalysisReport | None:
        model = await self._session.get(AnalysisReportModel, report_id)
        return _to_entity(model) if model else None


def _to_model(report: AnalysisReport) -> AnalysisReportModel:
    return AnalysisReportModel(
        id=report.id,
        summary=report.summary,
        period_start=report.period_start,
        period_end=report.period_end,
        alert_ids=[str(alert_id) for alert_id in report.alert_ids],
        generated_at=report.generated_at,
        s3_object_key=report.s3_object_key,
    )


def _to_entity(model: AnalysisReportModel) -> AnalysisReport:
    from uuid import UUID as UUIDType

    return AnalysisReport(
        id=model.id,
        summary=model.summary,
        period_start=model.period_start,
        period_end=model.period_end,
        alert_ids=[UUIDType(alert_id) for alert_id in (model.alert_ids or [])],
        generated_at=model.generated_at,
        s3_object_key=model.s3_object_key,
    )
