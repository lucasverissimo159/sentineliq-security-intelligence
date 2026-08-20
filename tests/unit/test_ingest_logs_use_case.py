"""Unit tests for IngestLogsUseCase using fake ports (no real DB/AWS)."""
from __future__ import annotations

import pytest

from sentineliq.application.use_cases.ingest_logs import IngestLogsUseCase
from sentineliq.domain.exceptions import InvalidLogBatchError


async def test_ingest_logs_persists_and_archives(
    fake_log_repository, fake_object_storage, sample_log_entry
):
    use_case = IngestLogsUseCase(
        log_repository=fake_log_repository,
        object_storage=fake_object_storage,
    )

    result = await use_case.execute([sample_log_entry])

    assert result == [sample_log_entry]
    assert sample_log_entry in fake_log_repository.saved
    assert len(fake_object_storage.objects) == 1


async def test_ingest_logs_rejects_empty_batch(fake_log_repository, fake_object_storage):
    use_case = IngestLogsUseCase(
        log_repository=fake_log_repository,
        object_storage=fake_object_storage,
    )

    with pytest.raises(InvalidLogBatchError):
        await use_case.execute([])
