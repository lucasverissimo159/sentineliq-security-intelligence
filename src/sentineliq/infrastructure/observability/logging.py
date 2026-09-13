"""Structured logging and request correlation helpers for FastAPI.

Keeps logs readable from a single place without tying the domain layer
or application layer to any particular logger backend.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Adds a request_id field in every log record when present."""

    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_id_ctx.get()
        if request_id:
            record.request_id = request_id
        else:
            record.request_id = "-"
        return True


class JsonFormatter(logging.Formatter):
    """Small JSON-like formatter for structured logs when running locally."""

    def format(self, record: logging.LogRecord) -> str:
        extras = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "request_id": getattr(record, "request_id", "-"),
        }
        return f"{extras}"


def setup_logging() -> None:
    """Initializes a structured-console logger used in the FastAPI app."""
    level = os.getenv("SENTINELIQ_LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger("sentineliq")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.addFilter(RequestIdFilter())
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)


def request_id() -> str:
    return request_id_ctx.get() or str(uuid.uuid4())
