"""Endpoints for generating natural-language incident reports."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from sentineliq.application.use_cases.generate_threat_report import (
    GenerateThreatReportUseCase,
)
from sentineliq.interfaces.api.dependencies import get_generate_report_use_case
from sentineliq.interfaces.api.schemas.report_schemas import (
    AnalysisReportOut,
    GenerateReportRequest,
)

router = APIRouter(prefix="/reports", tags=["reports"])


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
