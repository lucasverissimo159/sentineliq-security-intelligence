"""Unit tests for background tasks."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from sentineliq.interfaces.api.background_tasks import run_analysis_loop


@pytest.fixture
def mock_get_settings():
    with patch("sentineliq.interfaces.api.background_tasks.get_settings") as m:
        m.return_value.analysis_interval_minutes = 5
        yield m


@pytest.fixture
def mock_get_db_session():
    with patch("sentineliq.interfaces.api.background_tasks.get_db_session") as m:
        # Create an async generator fake
        async def fake_session_gen():
            yield AsyncMock()

        m.return_value = fake_session_gen()
        yield m


@pytest.fixture
def mock_use_case():
    with patch("sentineliq.interfaces.api.background_tasks.get_analyze_logs_use_case") as m:
        use_case_mock = AsyncMock()
        use_case_mock.execute.return_value = []
        m.return_value = use_case_mock
        yield m


@pytest.mark.asyncio
async def test_run_analysis_loop_cancellation_respects_sleep(
    mock_get_settings,
    mock_get_db_session,
    mock_use_case,
):
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        # If sleep is awaited, raise CancelledError immediately to break the infinite loop
        mock_sleep.side_effect = asyncio.CancelledError()

        await run_analysis_loop()

        mock_sleep.assert_called_once_with(300) # 5 minutes * 60 seconds
        mock_use_case.return_value.execute.assert_not_called()


@pytest.mark.asyncio
async def test_run_analysis_loop_executes_usecase(
    mock_get_settings,
    mock_get_db_session,
    mock_use_case,
):
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        # To test the execute loop without hanging forever, we need to let it sleep (do nothing),
        # let it execute the inner block, and then on the SECOND sleep, throw a CancelledError to exit.
        mock_sleep.side_effect = [None, asyncio.CancelledError()]

        await run_analysis_loop()

        assert mock_sleep.call_count == 2
        mock_use_case.return_value.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_analysis_loop_swallows_exceptions(
    mock_get_settings,
    mock_get_db_session,
    mock_use_case,
):
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        # Throw an exception during the execute step, and verify it doesn't crash the loop.
        mock_use_case.return_value.execute.side_effect = Exception("Transient Claude error")

        # We'll cancel on the second sleep to exit the infinite loop
        mock_sleep.side_effect = [None, asyncio.CancelledError()]

        await run_analysis_loop()

        # It should have called execute, caught the exception, logged it, and looped around to the second sleep
        mock_use_case.return_value.execute.assert_awaited_once()
        assert mock_sleep.call_count == 2
