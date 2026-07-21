"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Provide a test client for the FastAPI application."""
    return TestClient(create_app())
