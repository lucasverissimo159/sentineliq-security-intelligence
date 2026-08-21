"""Integration tests for the reports router endpoints."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from sentineliq.domain.entities.analysis_report import AnalysisReport
from sentineliq.interfaces.api.main import create_app
from tests.conftest import FakeReportRepository

app = create_app()

@pytest.fixture
def client():
    # Bypass API Key authentication for the integration tests
    app.dependency_overrides[
        __import__("sentineliq.interfaces.api.dependencies", fromlist=["verify_api_key"]).verify_api_key
    ] = lambda: None

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def fake_repo():
    return FakeReportRepository()


def test_get_report_success(client, fake_repo):
    report_id = uuid.uuid4()
    report = AnalysisReport.new(
        summary="Integration test summary",
        period_start=datetime.now(UTC),
        period_end=datetime.now(UTC),
        alert_ids=[],
    )
    # Entities are frozen, cheat the ID for testing
    object.__setattr__(report, 'id', report_id)

    # Pre-populate our fake repo
    import asyncio
    asyncio.run(fake_repo.save(report))

    app.dependency_overrides[
        __import__("sentineliq.interfaces.api.dependencies", fromlist=["get_report_repository"]).get_report_repository
    ] = lambda: fake_repo

    response = client.get(f"/reports/{report_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report_id)
    assert data["summary"] == "Integration test summary"


def test_get_report_not_found(client, fake_repo):
    app.dependency_overrides[
        __import__("sentineliq.interfaces.api.dependencies", fromlist=["get_report_repository"]).get_report_repository
    ] = lambda: fake_repo

    missing_id = uuid.uuid4()
    response = client.get(f"/reports/{missing_id}")

    assert response.status_code == 404
    assert str(missing_id) in response.json()["detail"]
