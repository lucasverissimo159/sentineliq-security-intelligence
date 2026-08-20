"""Use cases: application-specific orchestration of ports and domain entities.

Each use case is a single, focused operation (ingest, analyze,
report). They contain no I/O logic of their own — they only call
methods on the ports injected into them — which is what makes them
trivially unit-testable with fakes (see `tests/unit`).
"""
from sentineliq.application.use_cases.analyze_logs import AnalyzeLogsUseCase
from sentineliq.application.use_cases.generate_threat_report import (
    GenerateThreatReportUseCase,
)
from sentineliq.application.use_cases.ingest_logs import IngestLogsUseCase

__all__ = ["IngestLogsUseCase", "AnalyzeLogsUseCase", "GenerateThreatReportUseCase"]
