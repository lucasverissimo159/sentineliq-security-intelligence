"""Use case: ingest a batch of log entries."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.application.ports.object_storage import ObjectStoragePort
from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.exceptions import InvalidLogBatchError


@dataclass(slots=True)
class IngestLogsUseCase:
    """Persist an incoming batch of logs and archive the raw payload to S3.

    Two side effects, one use case: the batch is written to PostgreSQL
    (queryable, structured) and the original payload is archived to S3
    (cheap, durable, replayable). Both ports are injected, so this
    class has zero knowledge of SQLAlchemy or boto3.
    """

    log_repository: LogRepositoryPort
    object_storage: ObjectStoragePort

    async def execute(self, log_entries: list[LogEntry]) -> list[LogEntry]:
        if not log_entries:
            raise InvalidLogBatchError("Cannot ingest an empty batch of logs.")

        await self.log_repository.save_many(log_entries)
        await self._archive_raw_batch(log_entries)
        return log_entries

    async def _archive_raw_batch(self, log_entries: list[LogEntry]) -> None:
        timestamp = datetime.now(UTC).strftime("%Y/%m/%d/%H%M%S")
        key = f"raw-batches/{timestamp}-{log_entries[0].id}.json"
        payload = json.dumps(
            [
                {
                    "id": str(entry.id),
                    "source": entry.source,
                    "raw_message": entry.raw_message,
                    "severity": entry.severity.name,
                    "occurred_at": entry.occurred_at.isoformat(),
                    "metadata": entry.metadata,
                }
                for entry in log_entries
            ]
        ).encode("utf-8")
        await self.object_storage.upload(key, payload)
