"""Shared pytest fixtures.

Fakes for the application ports live here so unit tests can exercise
use cases with zero real infrastructure (no DB, no AWS, no Anthropic
API key) — the payoff of depending on abstractions instead of
concrete adapters.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.application.ports.api_key_repository import ApiKeyRepositoryPort
from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.application.ports.object_storage import ObjectStoragePort
from sentineliq.application.ports.report_repository import ReportRepositoryPort
from sentineliq.domain.entities.analysis_report import AnalysisReport
from sentineliq.domain.entities.api_key import ApiKey
from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.value_objects.severity import Severity


class FakeLogRepository(LogRepositoryPort):
    def __init__(self) -> None:
        self.saved: list[LogEntry] = []

    async def save_many(self, log_entries: list[LogEntry]) -> None:
        self.saved.extend(log_entries)

    async def find_by_id(self, log_id: UUID) -> LogEntry | None:
        return next((log for log in self.saved if log.id == log_id), None)

    async def find_since(self, since: datetime, limit: int = 500) -> list[LogEntry]:
        return [log for log in self.saved if log.occurred_at >= since][:limit]


class FakeAlertRepository(AlertRepositoryPort):
    def __init__(self) -> None:
        self.saved: list[ThreatAlert] = []

    async def save_many(self, alerts: list[ThreatAlert]) -> None:
        self.saved.extend(alerts)

    async def find_by_id(self, alert_id: UUID) -> ThreatAlert | None:
        return next((a for a in self.saved if a.id == alert_id), None)

    async def list_unacknowledged(self, limit: int = 100) -> list[ThreatAlert]:
        return [a for a in self.saved if not a.acknowledged][:limit]

    async def update(self, alert: ThreatAlert) -> None:
        for i, a in enumerate(self.saved):
            if a.id == alert.id:
                self.saved[i] = alert
                break


class FakeObjectStorage(ObjectStoragePort):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload(self, key: str, content: bytes, content_type: str = "application/json") -> str:
        self.objects[key] = content
        return f"fake://{key}"

    async def download(self, key: str) -> bytes:
        return self.objects[key]


class FakeApiKeyRepository(ApiKeyRepositoryPort):
    def __init__(self) -> None:
        self.saved: list[ApiKey] = []

    async def find_by_hash(self, key_hash: str) -> ApiKey | None:
        return next((k for k in self.saved if k.key_hash == key_hash), None)

    async def save(self, api_key: ApiKey) -> None:
        existing = await self.find_by_hash(api_key.key_hash)
        if existing:
            self.saved.remove(existing)
        self.saved.append(api_key)


class FakeReportRepository(ReportRepositoryPort):
    def __init__(self) -> None:
        self.saved: list[AnalysisReport] = []

    async def save(self, report: AnalysisReport) -> None:
        self.saved.append(report)

    async def find_by_id(self, report_id: UUID) -> AnalysisReport | None:
        return next((r for r in self.saved if r.id == report_id), None)


class FakeAIAnalysis(AIAnalysisPort):
    """Returns canned results instead of calling the real Claude API."""

    def __init__(self) -> None:
        self.anomalies_to_return: list[ThreatAlert] = []
        self.summary_to_return: str = "Fake summary."

    async def detect_anomalies(self, logs: list[LogEntry]) -> list[ThreatAlert]:
        return self.anomalies_to_return

    async def summarize(self, logs: list[LogEntry], alerts: list[ThreatAlert]) -> str:
        return self.summary_to_return


@pytest.fixture
def fake_log_repository() -> FakeLogRepository:
    return FakeLogRepository()


@pytest.fixture
def fake_alert_repository() -> FakeAlertRepository:
    return FakeAlertRepository()


@pytest.fixture
def fake_object_storage() -> FakeObjectStorage:
    return FakeObjectStorage()


@pytest.fixture
def fake_ai_analysis() -> FakeAIAnalysis:
    return FakeAIAnalysis()


@pytest.fixture
def fake_api_key_repository() -> FakeApiKeyRepository:
    return FakeApiKeyRepository()


@pytest.fixture
def fake_report_repository() -> FakeReportRepository:
    return FakeReportRepository()


@pytest.fixture
def sample_log_entry() -> LogEntry:
    return LogEntry.new(
        source="firewall-edge-01",
        raw_message="Blocked inbound connection from 203.0.113.4:443",
        severity=Severity.MEDIUM,
        occurred_at=datetime.now(UTC),
    )
