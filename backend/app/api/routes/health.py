"""Health check endpoints."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return application health status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
    }
