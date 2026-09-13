"""Smoke test for the FastAPI app wiring itself together correctly."""
from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from sentineliq.interfaces.api.main import create_app


async def test_health_check_returns_ok():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] in {"ok", "degraded"}
    assert payload["app"] == "SentinelIQ"
    assert payload["env"] == "development"
    assert "services" in payload
    assert "database" in payload["services"]
    assert "object_storage" in payload["services"]
    assert "ai_analysis" in payload["services"]


async def test_root_metadata_returns_project_snapshot():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    payload = response.json()
    assert response.status_code == 200
    assert payload["app"] == "SentinelIQ"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "development"
    assert payload["docs"] == "/docs"
    assert payload["ui"] == "/ui"
    assert "endpoints" in payload
