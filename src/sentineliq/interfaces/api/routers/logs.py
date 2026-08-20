"""Endpoints for ingesting and browsing log entries."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from sentineliq.application.use_cases.ingest_logs import IngestLogsUseCase
from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.value_objects.severity import Severity
from sentineliq.infrastructure.persistence.repositories.postgres_log_repository import (
    PostgresLogRepository,
)
from sentineliq.interfaces.api.dependencies import get_ingest_logs_use_case, get_log_repository
from sentineliq.interfaces.api.schemas.log_schemas import (
    LogEntryOut,
    LogIngestRequest,
    LogIngestResponse,
)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=LogIngestResponse, status_code=201)
async def ingest_logs(
    payload: LogIngestRequest,
    use_case: IngestLogsUseCase = Depends(get_ingest_logs_use_case),
) -> LogIngestResponse:
    entries = [
        LogEntry.new(
            source=item.source,
            raw_message=item.raw_message,
            severity=Severity.from_string(item.severity),
            occurred_at=item.occurred_at,
            metadata=item.metadata,
        )
        for item in payload.logs
    ]
    saved = await use_case.execute(entries)
    return LogIngestResponse(
        ingested=len(saved),
        logs=[_to_out(entry) for entry in saved],
    )


@router.get("", response_model=list[LogEntryOut])
async def list_recent_logs(
    minutes: int = Query(60, ge=1, le=10080, description="How far back to look."),
    limit: int = Query(200, ge=1, le=2000),
    repository: PostgresLogRepository = Depends(get_log_repository),
) -> list[LogEntryOut]:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    entries = await repository.find_since(since, limit=limit)
    return [_to_out(entry) for entry in entries]


def _to_out(entry: LogEntry) -> LogEntryOut:
    return LogEntryOut(
        id=entry.id,
        source=entry.source,
        raw_message=entry.raw_message,
        severity=entry.severity.name,
        occurred_at=entry.occurred_at,
        ingested_at=entry.ingested_at,
        metadata=entry.metadata,
    )
