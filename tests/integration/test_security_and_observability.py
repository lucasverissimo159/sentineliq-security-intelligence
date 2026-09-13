"""Integration expectations for the new security and observability surfaces.

These tests are deliberately written as a regression guard for the
portfolio-grade documentation and HTTP contract that we are adding.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from sentineliq.domain.entities.threat_alert import ThreatAlert
from sentineliq.domain.value_objects.severity import Severity
from sentineliq.interfaces.api.dependencies import get_alert_repository
from sentineliq.interfaces.api.main import create_app
from tests.conftest import FakeAlertRepository


async def test_auth_token_and_me_endpoint_work():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_response = await client.post(
            "/auth/token",
            json={"username": "admin", "password": "admin"},
        )

        assert token_response.status_code == 200
        body = token_response.json()
        assert body["token_type"] == "bearer"
        assert "access_token" in body

        token = body["access_token"]
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["username"] == "admin"
    assert "scopes" in payload


async def test_acknowledge_endpoint_marks_alert_as_acknowledged():
    app = create_app()
    fake_repository = FakeAlertRepository()
    alert = ThreatAlert.new(
        title="Suspicious failed admin login",
        explanation="Multiple failed admin-login attempts detected in the same window.",
        severity=Severity.HIGH,
        related_log_ids=[uuid4()],
    )
    await fake_repository.save_many([alert])

    app.dependency_overrides[get_alert_repository] = lambda: fake_repository

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/alerts/{alert.id}/acknowledge")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(alert.id)
    assert body["acknowledged"] is True
    assert fake_repository.saved[0].acknowledged is True


async def test_metrics_endpoint_exposes_prometheus_text():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert b"sentineliq_requests_total" in response.content
