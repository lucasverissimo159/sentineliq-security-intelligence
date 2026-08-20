"""Unit tests for API key authentication dependency."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from sentineliq.domain.entities.api_key import ApiKey
from sentineliq.interfaces.api.dependencies import verify_api_key
from tests.conftest import FakeApiKeyRepository


@pytest.mark.asyncio
async def test_verify_api_key_valid(fake_api_key_repository: FakeApiKeyRepository):
    entity, raw_key = ApiKey.new(name="test-key")
    await fake_api_key_repository.save(entity)

    # Should not raise
    result = await verify_api_key(raw_key=raw_key, api_key_repo=fake_api_key_repository)
    assert result == entity


@pytest.mark.asyncio
async def test_verify_api_key_missing(fake_api_key_repository: FakeApiKeyRepository):
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(raw_key=None, api_key_repo=fake_api_key_repository)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing API key"


@pytest.mark.asyncio
async def test_verify_api_key_invalid(fake_api_key_repository: FakeApiKeyRepository):
    entity, _ = ApiKey.new(name="test-key")
    await fake_api_key_repository.save(entity)

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(raw_key="invalid-key-value", api_key_repo=fake_api_key_repository)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or inactive API key"


@pytest.mark.asyncio
async def test_verify_api_key_inactive(fake_api_key_repository: FakeApiKeyRepository):
    entity, raw_key = ApiKey.new(name="test-key")
    entity.is_active = False
    await fake_api_key_repository.save(entity)

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(raw_key=raw_key, api_key_repo=fake_api_key_repository)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or inactive API key"
