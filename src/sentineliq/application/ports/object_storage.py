"""Object storage boundary — fulfilled today by the AWS S3 adapter."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ObjectStoragePort(ABC):
    """Contract for archiving raw payloads to durable object storage.

    Kept intentionally narrow (upload/download by key) so the
    application layer never has to know it's talking to S3
    specifically — only that it can archive and retrieve bytes.
    """

    @abstractmethod
    async def upload(self, key: str, content: bytes, content_type: str = "application/json") -> str:
        """Upload `content` under `key`. Returns the storage URI."""

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download the object stored under `key`."""
