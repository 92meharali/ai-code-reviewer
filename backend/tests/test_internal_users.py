"""Tests for internal user CRUD endpoints."""

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture
def client_with_db() -> Iterator[TestClient]:
    """Provide a test client with an in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def setup_database() -> async_sessionmaker[AsyncSession]:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import asyncio

    session_factory = asyncio.run(setup_database())

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def test_create_user_returns_201(client_with_db: TestClient) -> None:
    """POST /internal/users should create a user."""
    response = client_with_db.post(
        "/internal/users",
        json={
            "github_id": 12345,
            "username": "octocat",
            "email": "octocat@github.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["github_id"] == 12345
    assert data["username"] == "octocat"
    assert data["email"] == "octocat@github.com"
    assert "id" in data
    assert "created_at" in data


def test_create_duplicate_github_id_returns_409(client_with_db: TestClient) -> None:
    """POST /internal/users should reject duplicate GitHub IDs."""
    payload = {"github_id": 555, "username": "first-user"}
    client_with_db.post("/internal/users", json=payload)

    response = client_with_db.post(
        "/internal/users",
        json={"github_id": 555, "username": "second-user"},
    )

    assert response.status_code == 409


def test_list_users_returns_created_users(client_with_db: TestClient) -> None:
    """GET /internal/users should return all users."""
    client_with_db.post(
        "/internal/users",
        json={"github_id": 1, "username": "user-one"},
    )
    client_with_db.post(
        "/internal/users",
        json={"github_id": 2, "username": "user-two"},
    )

    response = client_with_db.get("/internal/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["username"] == "user-one"
    assert data[1]["username"] == "user-two"


def test_get_user_returns_user_by_id(client_with_db: TestClient) -> None:
    """GET /internal/users/{id} should return a single user."""
    create_response = client_with_db.post(
        "/internal/users",
        json={"github_id": 77, "username": "lookup-user"},
    )
    user_id = create_response.json()["id"]

    response = client_with_db.get(f"/internal/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["username"] == "lookup-user"


def test_get_missing_user_returns_404(client_with_db: TestClient) -> None:
    """GET /internal/users/{id} should return 404 for unknown users."""
    response = client_with_db.get("/internal/users/9999")

    assert response.status_code == 404


def test_delete_user_returns_204(client_with_db: TestClient) -> None:
    """DELETE /internal/users/{id} should remove the user."""
    create_response = client_with_db.post(
        "/internal/users",
        json={"github_id": 88, "username": "delete-user"},
    )
    user_id = create_response.json()["id"]

    delete_response = client_with_db.delete(f"/internal/users/{user_id}")
    get_response = client_with_db.get(f"/internal/users/{user_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
