"""Async database engine and session management."""

import logging
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    """Initialize the async database engine and session factory."""
    global engine, async_session_factory

    engine = create_async_engine(database_url, pool_pre_ping=True)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("Database engine initialized")


async def close_db() -> None:
    """Dispose of the database engine and release connections."""
    global engine, async_session_factory

    if engine is not None:
        await engine.dispose()
        logger.info("Database engine disposed")

    engine = None
    async_session_factory = None


async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide a database session for request-scoped dependency injection."""
    if async_session_factory is None:
        raise RuntimeError("Database is not initialized")

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """Verify the database is reachable."""
    if engine is None:
        return False

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False
