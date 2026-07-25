"""GitHub OAuth integration."""

import logging
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.schemas.github import GitHubUserProfile

logger = logging.getLogger(__name__)


class GitHubOAuthError(Exception):
    """Raised when a GitHub OAuth operation fails."""


class GitHubOAuthService:
    """Client for GitHub OAuth authorization and user profile retrieval."""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_API_URL = "https://api.github.com/user"
    EMAILS_API_URL = "https://api.github.com/user/emails"

    def __init__(self, settings: Settings) -> None:
        self._client_id = settings.github_client_id
        self._client_secret = settings.github_client_secret
        self._redirect_uri = settings.github_oauth_redirect_uri
        self._scopes = settings.github_oauth_scopes

    @property
    def is_configured(self) -> bool:
        """Return whether the required OAuth settings are present."""
        return bool(self._client_id and self._client_secret and self._redirect_uri)

    def get_authorization_url(self, state: str) -> str:
        """Build the GitHub authorization URL."""
        self._ensure_configured()

        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "scope": self._scopes,
                "state": state,
            }
        )
        return f"{self.AUTHORIZE_URL}?{query}"

    async def exchange_code_for_token(self, code: str) -> str:
        """Exchange an authorization code for a GitHub access token."""
        self._ensure_configured()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.TOKEN_URL,
                    headers={"Accept": "application/json"},
                    json={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": self._redirect_uri,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Failed to exchange GitHub OAuth code for token")
            raise GitHubOAuthError("Failed to exchange authorization code") from exc

        access_token = payload.get("access_token")
        if not access_token:
            error_description = payload.get("error_description", "Missing access token")
            raise GitHubOAuthError(error_description)

        return access_token

    async def get_user_profile(self, access_token: str) -> GitHubUserProfile:
        """Fetch and normalize the authenticated GitHub user's profile."""
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                user_response = await client.get(self.USER_API_URL, headers=headers)
                user_response.raise_for_status()
                user_data = user_response.json()

                email = user_data.get("email")
                if email is None:
                    email = await self._fetch_primary_email(client, headers)
        except httpx.HTTPError as exc:
            logger.exception("Failed to fetch GitHub user profile")
            raise GitHubOAuthError("Failed to fetch GitHub user profile") from exc

        return GitHubUserProfile(
            id=user_data["id"],
            login=user_data["login"],
            email=email,
            avatar_url=user_data.get("avatar_url"),
        )

    async def _fetch_primary_email(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
    ) -> str | None:
        """Return the user's primary email address when it is not public."""
        response = await client.get(self.EMAILS_API_URL, headers=headers)
        response.raise_for_status()
        emails = response.json()

        for entry in emails:
            if entry.get("primary"):
                return entry.get("email")

        if emails:
            return emails[0].get("email")

        return None

    def _ensure_configured(self) -> None:
        """Validate that OAuth settings are available."""
        if not self.is_configured:
            raise GitHubOAuthError("GitHub OAuth is not configured")
