"""Endpoints for triggering analysis and browsing threat alerts."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from sentineliq.application.use_cases.analyze_logs import AnalyzeLogsUseCase
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.infrastructure.persistence.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from sentineliq.interfaces.api.dependencies import get_alert_repository, get_analyze_logs_use_case
from sentineliq.interfaces.api.schemas.alert_schemas import AnalyzeLogsResponse, ThreatAlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


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
