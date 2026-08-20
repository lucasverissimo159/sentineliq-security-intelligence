"""Smoke test for the FastAPI app wiring itself together correctly."""
from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from sentineliq.interfaces.api.main import create_app


async def test_health_check_returns_ok():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
