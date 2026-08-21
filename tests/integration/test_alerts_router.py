"""Integration tests for the alerts router endpoints."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from sentineliq.domain.exceptions import ThreatAlertNotFoundError
from sentineliq.interfaces.api.main import create_app

app = create_app()

@pytest.fixture
def client():
    # Bypass API Key authentication for the integration tests
    app.dependency_overrides[
        __import__("sentineliq.interfaces.api.dependencies", fromlist=["verify_api_key"]).verify_api_key
    ] = lambda: None

    yield TestClient(app)

    app.dependency_overrides.clear()

def test_acknowledge_alert_success(client):
    alert_id = uuid.uuid4()

    with patch("sentineliq.interfaces.api.routers.alerts.get_acknowledge_alert_use_case") as mock_use_case_factory:
        mock_use_case = AsyncMock()
        mock_use_case_factory.return_value = mock_use_case

        # We need to override the dependency directly in FastAPI, but since we are patching the
        # function that provides the use case, Depends() will pick up the mocked factory instead.
        app.dependency_overrides[
            # Depends() uses the function reference to look up overrides
            __import__("sentineliq.interfaces.api.dependencies", fromlist=["get_acknowledge_alert_use_case"]).get_acknowledge_alert_use_case
        ] = lambda: mock_use_case

        response = client.post(f"/alerts/{alert_id}/acknowledge")

        assert response.status_code == 204
        mock_use_case.execute.assert_awaited_once_with(alert_id)

        # Clean up overrides
        app.dependency_overrides.clear()

def test_acknowledge_alert_not_found(client):
    alert_id = uuid.uuid4()

    with patch("sentineliq.interfaces.api.routers.alerts.get_acknowledge_alert_use_case") as mock_use_case_factory:
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ThreatAlertNotFoundError(alert_id)
        mock_use_case_factory.return_value = mock_use_case

        app.dependency_overrides[
            __import__("sentineliq.interfaces.api.dependencies", fromlist=["get_acknowledge_alert_use_case"]).get_acknowledge_alert_use_case
        ] = lambda: mock_use_case

        response = client.post(f"/alerts/{alert_id}/acknowledge")

        assert response.status_code == 404
        assert str(alert_id) in response.json()["detail"]

        app.dependency_overrides.clear()
