"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_check_returns_healthy_status(client: TestClient) -> None:
    """Health endpoint should return 200 with expected payload."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "AI Code Reviewer"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
    assert data["database"] == "connected"


def test_health_check_returns_unhealthy_when_database_down(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Health endpoint should return 503 when the database is unreachable."""
    async def mock_check_database_connection() -> bool:
        return False

    monkeypatch.setattr(
        "app.api.routes.health.check_database_connection",
        mock_check_database_connection,
    )

    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()["detail"]
    assert data["status"] == "unhealthy"
    assert data["database"] == "disconnected"
