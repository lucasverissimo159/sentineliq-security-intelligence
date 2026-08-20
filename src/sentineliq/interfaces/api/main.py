"""FastAPI application factory and entrypoint.

Run locally with:
    uvicorn sentineliq.interfaces.api.main:app --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sentineliq.infrastructure.config.settings import get_settings
from sentineliq.infrastructure.persistence.database import get_engine
from sentineliq.interfaces.api.routers import alerts, logs, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    yield
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

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

    return app


app = create_app()
