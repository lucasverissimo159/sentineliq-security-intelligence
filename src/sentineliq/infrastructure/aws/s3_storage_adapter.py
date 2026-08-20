"""AWS S3 implementation of ObjectStoragePort."""
from __future__ import annotations

import asyncio
from functools import cached_property

import boto3
from botocore.client import BaseClient

from sentineliq.application.ports.object_storage import ObjectStoragePort
from sentineliq.infrastructure.config.settings import Settings


class S3ObjectStorageAdapter(ObjectStoragePort):
    """Fulfills ObjectStoragePort using boto3 against an AWS S3 bucket.

    boto3 is synchronous, so calls are pushed to a worker thread via
    `asyncio.to_thread` to avoid blocking the event loop. This keeps
    the dependency footprint small (no aioboto3) while still exposing
    a fully async port to the rest of the application.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @cached_property
    def _client(self) -> BaseClient:
        return boto3.client(
            "s3",
            region_name=self._settings.aws_region,
            aws_access_key_id=self._settings.aws_access_key_id,
            aws_secret_access_key=self._settings.aws_secret_access_key,
        )

    async def upload(self, key: str, content: bytes, content_type: str = "application/json") -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._settings.aws_s3_bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return f"s3://{self._settings.aws_s3_bucket}/{key}"

    async def download(self, key: str) -> bytes:
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._settings.aws_s3_bucket,
            Key=key,
        )
        return response["Body"].read()
