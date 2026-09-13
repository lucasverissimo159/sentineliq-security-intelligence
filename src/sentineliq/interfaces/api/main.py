"""FastAPI application factory and entrypoint.

Run locally with:
    uvicorn sentineliq.interfaces.api.main:app --reload
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sentineliq.domain.exceptions import DomainError
from sentineliq.infrastructure.config.settings import get_settings
from sentineliq.infrastructure.observability.logging import request_id, setup_logging
from sentineliq.infrastructure.observability.metrics import REQUESTS_TOTAL, generate_latest
from sentineliq.infrastructure.observability.tracing import trace_span
from sentineliq.infrastructure.persistence.database import get_engine
from sentineliq.interfaces.api.background_tasks import run_analysis_loop
from sentineliq.interfaces.api.routers import alerts, auth, logs, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging()
    logging.basicConfig(level=settings.log_level)

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


def _service_status(settings) -> dict[str, dict[str, str]]:
    """Return a safe configuration snapshot for infrastructure probes.

    This keeps the health endpoint useful for operators and recruiters
    without echoing credentials or connection strings into the browser.
    """

    database = {
        "provider": "PostgreSQL",
        "status": "configured" if settings.database_url else "not_configured",
    }
    object_storage = {
        "provider": "AWS S3",
        "status": "configured" if settings.aws_s3_bucket else "not_configured",
        "bucket": settings.aws_s3_bucket,
    }
    ai_analysis = {
        "provider": "Anthropic Claude",
        "status": "configured" if settings.anthropic_api_key else "not_configured",
        "model": settings.anthropic_model,
    }

    return {
        "database": database,
        "object_storage": object_storage,
        "ai_analysis": ai_analysis,
    }


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

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "domain_error",
                    "message": str(exc),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": exc.detail,
                }
            },
        )

    app.include_router(auth.router)
    app.include_router(logs.router)
    app.include_router(alerts.router)
    app.include_router(reports.router)

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id_value = request.headers.get("X-Request-ID", request_id())
        with trace_span("HTTP request"):
            REQUESTS_TOTAL.inc()
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id_value
            return response

    @app.get("/metrics", tags=["metrics"])
    async def metrics_endpoint() -> PlainTextResponse:
        return PlainTextResponse(generate_latest().decode("utf-8"))

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, object]:
        services = _service_status(settings)
        configured_count = sum(
            1
            for service in services.values()
            if service["status"] == "configured"
        )
        degraded = configured_count < len(services)
        return {
            "status": "degraded" if degraded else "ok",
            "app": settings.app_name,
            "env": settings.app_env,
            "services": services,
        }

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, object]:
        return {
            "app": settings.app_name,
            "version": "0.1.0",
            "environment": settings.app_env,
            "description": (
                "AI-powered security log intelligence platform for ingesting logs, "
                "analyzing anomalies, and generating incident reports."
            ),
            "docs": "/docs",
            "ui": "/ui",
            "endpoints": {
                "logs": "/logs",
                "alerts": "/alerts",
                "alerts_analyze": "/alerts/analyze",
                "reports_generate": "/reports/generate",
            },
        }

    @app.get("/ui", tags=["ui"])
    async def ui_home() -> HTMLResponse:
        html = """
        <html>
        <head>
            <title>SentinelIQ</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 2rem; color: #102a43; }
                .card { border: 1px solid #d7e2ea; border-radius: 8px; padding: 1rem; max-width: 800px; }
                .badge { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px; background: #e6f4ea; color: #14532d; }
                code { background: #eef2f6; padding: 0.2rem; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>SentinelIQ</h1>
                <span class="badge">AI Security Intelligence</span>
                <p>Ingest logs, analyze anomalies, and generate incident summaries.</p>
                <ul>
                    <li><code>POST /logs</code> ingest log batch</li>
                    <li><code>GET /logs</code> list recent logs</li>
                    <li><code>POST /alerts/analyze</code> run analysis</li>
                    <li><code>GET /alerts</code> list alerts</li>
                    <li><code>POST /reports/generate</code> generate report</li>
                </ul>
                <p><a href="/docs">Open API docs</a> | <a href="/health">Health</a></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    return app


app = create_app()
