"""Background tasks running in the FastAPI lifespan."""
from __future__ import annotations

import asyncio
import logging

from sentineliq.infrastructure.config.settings import get_settings
from sentineliq.interfaces.api.dependencies import (
    get_ai_analysis,
    get_alert_repository,
    get_analyze_logs_use_case,
    get_db_session,
    get_log_repository,
)

logger = logging.getLogger(__name__)


async def run_analysis_loop() -> None:
    """Infinite loop that triggers background log analysis periodically.

    Sleeps for the configured interval, instantiates the AnalyzeLogsUseCase,
    and runs it, catching and logging any exceptions so the app does not crash.
    """
    settings = get_settings()
    interval_seconds = settings.analysis_interval_minutes * 60

    logger.info(f"Background analysis task started, running every {settings.analysis_interval_minutes} minutes.")

    while True:
        try:
            await asyncio.sleep(interval_seconds)

            # Resolve dependencies manually for the background context
            # (In a real app with a heavy DI container, this might be simpler,
            # but here we instantiate the adapters manually using the dependency factories)

            # Since get_db_session yields an AsyncIterator, we need to iterate it.
            # We use anext() to get the first (and only) yielded session, and we don't
            # manage the commit/rollback here directly since it's an async generator.
            # To be safer and strictly follow the generator protocol, we can just instantiate
            # the repositories using a direct session if we bypass get_db_session, or we can use it properly.

            # To handle the session properly outside of FastAPI's request lifecycle,
            # we iterate through the generator to yield the session, run the logic,
            # and then advance the generator again so it hits its `commit()` block.
            # Using `.aclose()` would trigger `GeneratorExit` and roll back.
            session_generator = get_db_session()
            session = await anext(session_generator)

            try:
                log_repo = get_log_repository(session)
                alert_repo = get_alert_repository(session)
                ai_analysis = get_ai_analysis(settings)

                use_case = get_analyze_logs_use_case(
                    log_repository=log_repo,
                    alert_repository=alert_repo,
                    ai_analysis=ai_analysis,
                )

                alerts_generated = await use_case.execute()

                # Advance the generator so it commits the transaction.
                try:
                    await anext(session_generator)
                except StopAsyncIteration:
                    pass

                logger.info(f"Background analysis run completed. Detected {len(alerts_generated)} alerts.")
            except Exception as inner_e:
                # Close the generator with an exception so it triggers a rollback
                try:
                    await session_generator.athrow(inner_e)
                except Exception:
                    pass

                # If an error happens inside the execute or setup, log it
                logger.exception(f"Error during background analysis run: {inner_e}")

        except asyncio.CancelledError:
            logger.info("Background analysis task cancelled. Shutting down gracefully.")
            break
        except Exception as e:
            logger.exception(f"Unexpected error in background analysis loop: {e}")
            # Do not re-raise or break here; wait until the next cycle to retry.
