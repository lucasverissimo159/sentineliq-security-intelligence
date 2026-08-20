"""Dependency injection wiring for the FastAPI layer.

This is the single place where abstract ports get bound to concrete
adapters. Use cases and routers only ever ask for a port type (via
`Depends(...)`); they never instantiate an adapter themselves. To swap
an adapter (e.g. a different AI provider, a different database), this
is the only file that changes.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.application.ports.api_key_repository import ApiKeyRepositoryPort
from sentineliq.domain.entities.api_key import ApiKey
from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.application.ports.object_storage import ObjectStoragePort
from sentineliq.application.use_cases.analyze_logs import AnalyzeLogsUseCase
from sentineliq.application.use_cases.generate_threat_report import (
    GenerateThreatReportUseCase,
)
from sentineliq.application.use_cases.ingest_logs import IngestLogsUseCase
from sentineliq.infrastructure.ai.claude_analysis_adapter import ClaudeAnalysisAdapter
from sentineliq.infrastructure.aws.s3_storage_adapter import S3ObjectStorageAdapter
from sentineliq.infrastructure.config.settings import Settings, get_settings
from sentineliq.infrastructure.persistence.database import get_session_factory
from sentineliq.infrastructure.persistence.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from sentineliq.infrastructure.persistence.repositories.postgres_api_key_repository import (
    PostgresApiKeyRepository,
)
from sentineliq.infrastructure.persistence.repositories.postgres_log_repository import (
    PostgresLogRepository,
)


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_log_repository(session: AsyncSession = Depends(get_db_session)) -> LogRepositoryPort:
    return PostgresLogRepository(session)


def get_alert_repository(session: AsyncSession = Depends(get_db_session)) -> AlertRepositoryPort:
    return PostgresAlertRepository(session)


def get_api_key_repository(session: AsyncSession = Depends(get_db_session)) -> ApiKeyRepositoryPort:
    return PostgresApiKeyRepository(session)


async def verify_api_key(
    raw_key: str | None = Security(api_key_header),
    api_key_repo: ApiKeyRepositoryPort = Depends(get_api_key_repository),
) -> ApiKey:
    """Validate the X-API-Key header and return the underlying entity."""
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_hash = ApiKey.hash_key(raw_key)
    api_key = await api_key_repo.find_by_hash(key_hash)

    if not api_key or not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def get_object_storage(settings: Settings = Depends(get_settings)) -> ObjectStoragePort:
    return S3ObjectStorageAdapter(settings)


def get_ai_analysis(settings: Settings = Depends(get_settings)) -> AIAnalysisPort:
    return ClaudeAnalysisAdapter(settings)


def get_ingest_logs_use_case(
    log_repository: LogRepositoryPort = Depends(get_log_repository),
    object_storage: ObjectStoragePort = Depends(get_object_storage),
) -> IngestLogsUseCase:
    return IngestLogsUseCase(log_repository=log_repository, object_storage=object_storage)


def get_analyze_logs_use_case(
    log_repository: LogRepositoryPort = Depends(get_log_repository),
    alert_repository: AlertRepositoryPort = Depends(get_alert_repository),
    ai_analysis: AIAnalysisPort = Depends(get_ai_analysis),
) -> AnalyzeLogsUseCase:
    return AnalyzeLogsUseCase(
        log_repository=log_repository,
        alert_repository=alert_repository,
        ai_analysis=ai_analysis,
    )


def get_generate_report_use_case(
    log_repository: LogRepositoryPort = Depends(get_log_repository),
    alert_repository: AlertRepositoryPort = Depends(get_alert_repository),
    ai_analysis: AIAnalysisPort = Depends(get_ai_analysis),
) -> GenerateThreatReportUseCase:
    return GenerateThreatReportUseCase(
        log_repository=log_repository,
        alert_repository=alert_repository,
        ai_analysis=ai_analysis,
    )
