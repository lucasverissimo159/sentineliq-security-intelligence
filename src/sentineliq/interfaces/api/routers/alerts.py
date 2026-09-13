"""Endpoints for triggering analysis and browsing threat alerts."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sentineliq.application.use_cases.analyze_logs import AnalyzeLogsUseCase
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.infrastructure.persistence.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from sentineliq.interfaces.api.dependencies import (
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


@router.post("/{alert_id}/acknowledge", response_model=ThreatAlertOut)
async def acknowledge_alert(
    alert_id: UUID,
    repository: PostgresAlertRepository = Depends(get_alert_repository),
) -> ThreatAlertOut:
    """Mark a threat alert as acknowledged and return the updated entity."""
    alert = await repository.acknowledge(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return _to_out(alert)


@router.get("", response_model=list[ThreatAlertOut])
async def list_unacknowledged_alerts(
    limit: int = Query(100, ge=1, le=1000),
    repository: PostgresAlertRepository = Depends(get_alert_repository),
) -> list[ThreatAlertOut]:
    alerts = await repository.list_unacknowledged(limit=limit)
    return [_to_out(a) for a in alerts]


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
