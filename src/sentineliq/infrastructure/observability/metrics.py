"""Minimal metrics container for the project.

Uses the Prometheus client library if runtime dependencies are installed;
keeps a no-op fallback so the project remains importable in tests.
"""
from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram, generate_latest
except Exception:  # pragma: no cover
    class _NoopMetric:
        def __init__(self, *args, **kwargs):
            return None

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

    def generate_latest():
        return b""

    class Counter(_NoopMetric):
        pass

    class Histogram(_NoopMetric):
        pass


REQUESTS_TOTAL = Counter("sentineliq_requests_total", "Total API requests")
REQUEST_LATENCY = Histogram("sentineliq_request_latency_seconds", "Request latency in seconds")
