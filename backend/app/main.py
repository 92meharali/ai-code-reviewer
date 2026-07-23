"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.routes import health
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown events."""
    settings = get_settings()
    setup_logging(settings)
    init_db(settings.database_url)
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        __version__,
        settings.environment,
    )
    yield
    await close_db()
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.include_router(health.router)

    if settings.environment == "development":
        from app.api.routes.internal import users as internal_users

        app.include_router(internal_users.router, prefix="/internal")

    return app


app = create_app()
