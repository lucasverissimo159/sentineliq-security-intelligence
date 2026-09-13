"""Lightweight tracing hook using OpenTelemetry-style context enrichment.

This repository remains import-safe in tests; the implementation is
forward-compatible with adding a real OpenTelemetry exporter later.
"""
from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def trace_span(name: str):
    """Yield a simple span-like context that is deliberately dependency-free."""
    try:
        yield {"name": name}
    except Exception:
        raise
