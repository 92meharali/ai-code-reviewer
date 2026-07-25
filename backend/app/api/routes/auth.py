"""GitHub OAuth authentication routes."""

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead
from app.services.github_oauth import GitHubOAuthError, GitHubOAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_MAX_AGE_SECONDS = 600


def get_github_oauth_service(
    settings: Settings = Depends(get_settings),
) -> GitHubOAuthService:
    """Provide a GitHub OAuth service instance."""
    return GitHubOAuthService(settings)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Provide a user repository bound to the request session."""
    return UserRepository(session)


@router.get("/github")
async def github_login(
    github_oauth: GitHubOAuthService = Depends(get_github_oauth_service),
) -> RedirectResponse:
    """Redirect the user to GitHub's OAuth authorization page."""
    if not github_oauth.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )

    state = secrets.token_urlsafe(32)
    redirect_response = RedirectResponse(
        url=github_oauth.get_authorization_url(state),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    redirect_response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        max_age=OAUTH_STATE_MAX_AGE_SECONDS,
        samesite="lax",
    )
    return redirect_response


@router.get("/github/callback", response_model=UserRead)
async def github_callback(
    request: Request,
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    github_oauth: GitHubOAuthService = Depends(get_github_oauth_service),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserRead:
    """Handle the GitHub OAuth callback and upsert the authenticated user."""
    response.delete_cookie(OAUTH_STATE_COOKIE)

    if error:
        detail = error_description or error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub OAuth error: {detail}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth code or state",
        )

    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if cookie_state is None or not secrets.compare_digest(cookie_state, state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        )

    if not github_oauth.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )

    try:
        access_token = await github_oauth.exchange_code_for_token(code)
        profile = await github_oauth.get_user_profile(access_token)
    except GitHubOAuthError as exc:
        logger.warning("GitHub OAuth callback failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    user = await user_repository.upsert_from_github(
        github_id=profile.id,
        username=profile.login,
        email=profile.email,
        avatar_url=profile.avatar_url,
    )
    return UserRead.model_validate(user)
