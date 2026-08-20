"""Abstract port for API key persistence."""
from __future__ import annotations

from typing import Protocol

from sentineliq.domain.entities.api_key import ApiKey


class ApiKeyRepositoryPort(Protocol):
    """Port for finding and saving ApiKey entities."""

    async def find_by_hash(self, key_hash: str) -> ApiKey | None:
        """Find an API key by its hash."""
        ...

    async def save(self, api_key: ApiKey) -> None:
        """Save a new or updated API key."""
        ...
