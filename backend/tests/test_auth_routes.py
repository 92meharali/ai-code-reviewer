"""Tests for GitHub OAuth authentication routes."""

from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.routes.auth import OAUTH_STATE_COOKIE, get_github_oauth_service
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.schemas.github import GitHubUserProfile
from app.services.github_oauth import GitHubOAuthService


@pytest.fixture
def oauth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure GitHub OAuth environment variables for tests."""
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv(
        "GITHUB_OAUTH_REDIRECT_URI",
        "http://testserver/auth/github/callback",
    )
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app_with_db(oauth_env: None) -> Iterator:
    """Provide an application instance backed by an in-memory database."""
    import asyncio

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def setup_database() -> async_sessionmaker[AsyncSession]:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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

    yield app

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


@pytest.fixture
def client_with_db(app_with_db) -> Iterator[TestClient]:
    """Provide a test client with an in-memory database."""
    with TestClient(app_with_db) as test_client:
        yield test_client


@pytest.fixture
def mock_github_oauth(app_with_db) -> GitHubOAuthService:
    """Provide a mocked GitHub OAuth service via dependency overrides."""
    service = GitHubOAuthService(
        Settings(
            github_client_id="test-client-id",
            github_client_secret="test-client-secret",
            github_oauth_redirect_uri="http://testserver/auth/github/callback",
        )
    )
    service.exchange_code_for_token = AsyncMock(return_value="gho_test_token")
    service.get_user_profile = AsyncMock(
        return_value=GitHubUserProfile(
            id=424242,
            login="octocat",
            email="octocat@github.com",
            avatar_url="https://avatars.githubusercontent.com/u/424242",
        )
    )
    app_with_db.dependency_overrides[get_github_oauth_service] = lambda: service
    return service


def test_github_login_redirects_to_github(client_with_db: TestClient) -> None:
    """GET /auth/github should redirect to GitHub and set the state cookie."""
    response = client_with_db.get("/auth/github", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith(
        "https://github.com/login/oauth/authorize"
    )
    assert OAUTH_STATE_COOKIE in response.cookies


def test_github_login_returns_503_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /auth/github should fail when OAuth credentials are missing."""
    monkeypatch.delenv("GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("GITHUB_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("GITHUB_OAUTH_REDIRECT_URI", raising=False)
    get_settings.cache_clear()

    with TestClient(create_app()) as client:
        response = client.get("/auth/github", follow_redirects=False)

    assert response.status_code == 503
    get_settings.cache_clear()


def test_github_callback_creates_user(
    client_with_db: TestClient,
    mock_github_oauth: GitHubOAuthService,
) -> None:
    """Callback should create a user from the GitHub profile."""
    login_response = client_with_db.get("/auth/github", follow_redirects=False)
    state = login_response.cookies[OAUTH_STATE_COOKIE]

    response = client_with_db.get(
        "/auth/github/callback",
        params={"code": "test-code", "state": state},
        cookies={OAUTH_STATE_COOKIE: state},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["github_id"] == 424242
    assert data["username"] == "octocat"
    assert data["email"] == "octocat@github.com"
    mock_github_oauth.exchange_code_for_token.assert_awaited_once_with("test-code")
    mock_github_oauth.get_user_profile.assert_awaited_once_with("gho_test_token")


def test_github_callback_updates_existing_user(
    client_with_db: TestClient,
    mock_github_oauth: GitHubOAuthService,
) -> None:
    """Callback should update an existing user with the latest GitHub profile."""
    login_response = client_with_db.get("/auth/github", follow_redirects=False)
    state = login_response.cookies[OAUTH_STATE_COOKIE]
    cookies = {OAUTH_STATE_COOKIE: state}

    first_response = client_with_db.get(
        "/auth/github/callback",
        params={"code": "first-code", "state": state},
        cookies=cookies,
    )
    user_id = first_response.json()["id"]

    mock_github_oauth.get_user_profile.return_value = GitHubUserProfile(
        id=424242,
        login="octocat-updated",
        email="new-email@github.com",
        avatar_url="https://avatars.githubusercontent.com/u/424242?v=2",
    )

    second_response = client_with_db.get(
        "/auth/github/callback",
        params={"code": "second-code", "state": state},
        cookies=cookies,
    )

    assert second_response.status_code == 200
    data = second_response.json()
    assert data["id"] == user_id
    assert data["username"] == "octocat-updated"
    assert data["email"] == "new-email@github.com"


def test_github_callback_rejects_invalid_state(
    client_with_db: TestClient,
    mock_github_oauth: GitHubOAuthService,
) -> None:
    """Callback should reject requests with an invalid OAuth state."""
    response = client_with_db.get(
        "/auth/github/callback",
        params={"code": "test-code", "state": "invalid-state"},
        cookies={OAUTH_STATE_COOKIE: "different-state"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid OAuth state"


def test_github_callback_returns_github_error(client_with_db: TestClient) -> None:
    """Callback should surface GitHub authorization errors."""
    response = client_with_db.get(
        "/auth/github/callback",
        params={
            "error": "access_denied",
            "error_description": "The user denied access",
            "state": "ignored",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "GitHub OAuth error: The user denied access"
