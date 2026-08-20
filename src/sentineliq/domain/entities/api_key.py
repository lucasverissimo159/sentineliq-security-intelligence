"""API Key domain entity."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class ApiKey:
    """Represents an API key used for authenticating requests."""

    id: UUID
    name: str
    key_hash: str
    created_at: datetime
    is_active: bool

    @classmethod
    def new(cls, name: str) -> tuple[ApiKey, str]:
        """Creates a new API key and returns the entity along with the raw key value.

        The raw key value is only available once at creation time and should be given to the user.
        """
        raw_key = secrets.token_urlsafe(32)
        key_hash = cls.hash_key(raw_key)

        entity = cls(
            id=uuid4(),
            name=name,
            key_hash=key_hash,
            created_at=datetime.now(UTC),
            is_active=True,
        )
        return entity, raw_key

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Hashes an API key for secure storage."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def verify(self, raw_key: str) -> bool:
        """Verifies if the provided raw key matches this API key's hash."""
        return self.is_active and self.hash_key(raw_key) == self.key_hash
