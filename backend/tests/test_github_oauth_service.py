"""Tests for the GitHub OAuth service."""

import pytest

from app.core.config import Settings
from app.services.github_oauth import GitHubOAuthError, GitHubOAuthService


@pytest.fixture
def oauth_service() -> GitHubOAuthService:
    """Provide a configured GitHub OAuth service."""
    settings = Settings(
        github_client_id="test-client-id",
        github_client_secret="test-client-secret",
        github_oauth_redirect_uri="http://localhost:8000/auth/github/callback",
        github_oauth_scopes="read:user user:email",
    )
    return GitHubOAuthService(settings)


def test_is_configured_returns_true_when_credentials_present(
    oauth_service: GitHubOAuthService,
) -> None:
    """Service should report configured when credentials are present."""
    assert oauth_service.is_configured is True


def test_is_configured_returns_false_when_credentials_missing() -> None:
    """Service should report unconfigured when credentials are missing."""
    service = GitHubOAuthService(Settings())

    assert service.is_configured is False


def test_get_authorization_url_includes_required_query_params(
    oauth_service: GitHubOAuthService,
) -> None:
    """Authorization URL should include client ID, redirect URI, scopes, and state."""
    url = oauth_service.get_authorization_url("state-token")

    assert url.startswith("https://github.com/login/oauth/authorize?")
    assert "client_id=test-client-id" in url
    assert "redirect_uri=http" in url
    assert "scope=read%3Auser+user%3Aemail" in url
    assert "state=state-token" in url


def test_get_authorization_url_requires_configuration() -> None:
    """Authorization URL generation should fail without OAuth settings."""
    service = GitHubOAuthService(Settings())

    with pytest.raises(GitHubOAuthError, match="not configured"):
        service.get_authorization_url("state-token")
