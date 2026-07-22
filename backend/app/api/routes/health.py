"""Health check endpoints."""

from fastapi import APIRouter, HTTPException

from app import __version__
from app.core.config import get_settings
from app.db.session import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return application and database health status."""
    settings = get_settings()
    database_healthy = await check_database_connection()

    payload = {
        "status": "healthy" if database_healthy else "unhealthy",
        "app": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "database": "connected" if database_healthy else "disconnected",
    }

    if not database_healthy:
        raise HTTPException(status_code=503, detail=payload)

    return payload
