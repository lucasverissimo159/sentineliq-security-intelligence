"""Endpoints for generating natural-language incident reports."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from sentineliq.application.ports.report_repository import ReportRepositoryPort
from sentineliq.application.use_cases.generate_threat_report import (
    GenerateThreatReportUseCase,
)
from sentineliq.domain.exceptions import AnalysisReportNotFoundError
from sentineliq.interfaces.api.dependencies import (
    get_generate_report_use_case,
    get_report_repository,
    verify_api_key,
)
from sentineliq.interfaces.api.schemas.report_schemas import (
    AnalysisReportOut,
    GenerateReportRequest,
)

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/generate", response_model=AnalysisReportOut)
async def generate_report(
    payload: GenerateReportRequest,
    use_case: GenerateThreatReportUseCase = Depends(get_generate_report_use_case),
) -> AnalysisReportOut:
    report = await use_case.execute(payload.period_start, payload.period_end)
    return AnalysisReportOut(
        id=report.id,
        summary=report.summary,
        period_start=report.period_start,
        period_end=report.period_end,
        alert_ids=report.alert_ids,
        generated_at=report.generated_at,
    )


@router.get("/{report_id}", response_model=AnalysisReportOut)
async def get_report(
    report_id: UUID,
    repository: ReportRepositoryPort = Depends(get_report_repository),
) -> AnalysisReportOut:
    report = await repository.find_by_id(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(AnalysisReportNotFoundError(report_id))
        )
    return AnalysisReportOut(
        id=report.id,
        summary=report.summary,
        period_start=report.period_start,
        period_end=report.period_end,
        alert_ids=report.alert_ids,
        generated_at=report.generated_at,
    )
