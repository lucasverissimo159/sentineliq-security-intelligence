"""Endpoints for triggering analysis and browsing threat alerts."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sentineliq.application.use_cases.acknowledge_alert import AcknowledgeAlertUseCase
from sentineliq.application.use_cases.analyze_logs import AnalyzeLogsUseCase
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.exceptions import ThreatAlertNotFoundError
from sentineliq.infrastructure.persistence.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from sentineliq.interfaces.api.dependencies import (
    get_acknowledge_alert_use_case,
    get_alert_repository,
    get_analyze_logs_use_case,
    verify_api_key,
)
from sentineliq.interfaces.api.schemas.alert_schemas import AnalyzeLogsResponse, ThreatAlertOut

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/analyze", response_model=AnalyzeLogsResponse)
async def analyze_recent_logs(
    use_case: AnalyzeLogsUseCase = Depends(get_analyze_logs_use_case),
) -> AnalyzeLogsResponse:
    """Trigger an on-demand analysis pass over the recent log window.

    In production this is also expected to run on a schedule; see
    docs/ROADMAP.md for suggested scheduling approaches.
    """
    alerts = await use_case.execute()
    return AnalyzeLogsResponse(alerts_found=len(alerts), alerts=[_to_out(a) for a in alerts])


@router.get("", response_model=list[ThreatAlertOut])
async def list_unacknowledged_alerts(
    limit: int = Query(100, ge=1, le=1000),
    repository: PostgresAlertRepository = Depends(get_alert_repository),
) -> list[ThreatAlertOut]:
    alerts = await repository.list_unacknowledged(limit=limit)
    return [_to_out(a) for a in alerts]


@router.post("/{alert_id}/acknowledge", status_code=status.HTTP_204_NO_CONTENT)
async def acknowledge_alert(
    alert_id: UUID,
    use_case: AcknowledgeAlertUseCase = Depends(get_acknowledge_alert_use_case),
):
    try:
        await use_case.execute(alert_id)
    except ThreatAlertNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


def _to_out(alert: ThreatAlert) -> ThreatAlertOut:
    return ThreatAlertOut(
        id=alert.id,
        title=alert.title,
        explanation=alert.explanation,
        severity=alert.severity.name,
        related_log_ids=alert.related_log_ids,
        detected_at=alert.detected_at,
        acknowledged=alert.acknowledged,
    )
