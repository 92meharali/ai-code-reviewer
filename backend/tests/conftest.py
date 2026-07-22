"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def mock_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock database lifecycle and connectivity for isolated API tests."""
    monkeypatch.setattr("app.main.init_db", lambda database_url: None)

    async def mock_close_db() -> None:
        return None

    monkeypatch.setattr("app.main.close_db", mock_close_db)

    async def mock_check_database_connection() -> bool:
        return True

    monkeypatch.setattr(
        "app.api.routes.health.check_database_connection",
        mock_check_database_connection,
    )


@pytest.fixture
def client() -> TestClient:
    """Provide a test client for the FastAPI application."""
    return TestClient(create_app())
