"""AWS adapters. Currently: S3 for raw log/report archival."""
from sentineliq.infrastructure.aws.s3_storage_adapter import S3ObjectStorageAdapter

__all__ = ["S3ObjectStorageAdapter"]
