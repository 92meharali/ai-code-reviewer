"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check_returns_healthy_status(client: TestClient) -> None:
    """Health endpoint should return 200 with expected payload."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "AI Code Reviewer"
    assert data["version"] == "0.1.0"
    assert "environment" in data
