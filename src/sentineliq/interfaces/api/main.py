"""FastAPI application factory and entrypoint.

Run locally with:
    uvicorn sentineliq.interfaces.api.main:app --reload
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from prometheus_fastapi_instrumentator import Instrumentator

from sentineliq.infrastructure.config.logging import setup_logging
from sentineliq.infrastructure.config.settings import get_settings
from sentineliq.infrastructure.persistence.database import get_engine
from sentineliq.interfaces.api.background_tasks import run_analysis_loop
from sentineliq.interfaces.api.routers import alerts, logs, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)

    # Start the background analysis loop
    analysis_task = asyncio.create_task(run_analysis_loop())

    yield

    # Cancel the background task and wait for it to finish
    analysis_task.cancel()
    try:
        await analysis_task
    except asyncio.CancelledError:
        pass

    # Dispose the SQLAlchemy engine's connection pool on shutdown.
    await get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI-powered security log intelligence platform. Ingests log data, "
            "detects anomalies, and generates natural-language incident reports "
            "using Claude, PostgreSQL, and AWS S3."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(logs.router)
    app.include_router(alerts.router)
    app.include_router(reports.router)

    @app.middleware("http")
    async def structlog_request_middleware(request: Request, call_next) -> Response:
        clear_contextvars()
        request_id = str(uuid4())
        bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

    # Setup basic Prometheus instrumentation (records request latency, counts, etc.)
    # and expose the /metrics endpoint
    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()
