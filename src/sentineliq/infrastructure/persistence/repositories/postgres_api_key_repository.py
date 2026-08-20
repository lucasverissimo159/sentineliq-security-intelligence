"""PostgreSQL adapter for the API key repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineliq.application.ports.api_key_repository import ApiKeyRepositoryPort
from sentineliq.domain.entities.api_key import ApiKey
from sentineliq.infrastructure.persistence.models import ApiKeyModel


class PostgresApiKeyRepository(ApiKeyRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_hash(self, key_hash: str) -> ApiKey | None:
        stmt = select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ApiKey(
            id=model.id,
            name=model.name,
            key_hash=model.key_hash,
            created_at=model.created_at,
            is_active=model.is_active,
        )

    async def save(self, api_key: ApiKey) -> None:
        model = ApiKeyModel(
            id=api_key.id,
            name=api_key.name,
            key_hash=api_key.key_hash,
            created_at=api_key.created_at,
            is_active=api_key.is_active,
        )
        self.session.add(model)
        # Flush to catch constraints without strictly committing yet
        await self.session.flush()
