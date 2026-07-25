"""Tests for user repository upsert behavior."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.repositories.user_repository import UserRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory database session for repository tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def repository(db_session: AsyncSession) -> UserRepository:
    """Provide a user repository bound to the test session."""
    return UserRepository(db_session)


async def test_upsert_from_github_creates_new_user(
    repository: UserRepository,
    db_session: AsyncSession,
) -> None:
    """Upsert should create a user when the GitHub ID does not exist."""
    user = await repository.upsert_from_github(
        github_id=1001,
        username="new-user",
        email="new-user@github.com",
    )
    await db_session.commit()

    assert user.id is not None
    assert user.github_id == 1001
    assert user.username == "new-user"


async def test_upsert_from_github_updates_existing_user(
    repository: UserRepository,
    db_session: AsyncSession,
) -> None:
    """Upsert should update profile fields for an existing GitHub user."""
    created_user = await repository.upsert_from_github(
        github_id=2002,
        username="old-name",
        email="old@github.com",
    )
    await db_session.commit()

    updated_user = await repository.upsert_from_github(
        github_id=2002,
        username="new-name",
        email="new@github.com",
        avatar_url="https://example.com/avatar.png",
    )
    await db_session.commit()

    assert updated_user.id == created_user.id
    assert updated_user.username == "new-name"
    assert updated_user.email == "new@github.com"
    assert updated_user.avatar_url == "https://example.com/avatar.png"
