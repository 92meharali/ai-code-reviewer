"""Tests for the user repository."""

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


async def test_create_user_persists_record(
    repository: UserRepository,
    db_session: AsyncSession,
) -> None:
    """Creating a user should persist it with expected fields."""
    user = await repository.create(
        github_id=12345,
        username="octocat",
        email="octocat@github.com",
        avatar_url="https://avatars.githubusercontent.com/u/12345",
    )
    await db_session.commit()

    assert user.id is not None
    assert user.github_id == 12345
    assert user.username == "octocat"
    assert user.email == "octocat@github.com"
    assert user.created_at is not None
    assert user.updated_at is not None


async def test_get_by_github_id_returns_user(
    repository: UserRepository,
    db_session: AsyncSession,
) -> None:
    """Repository should fetch users by GitHub ID."""
    created_user = await repository.create(
        github_id=99,
        username="hubot",
    )
    await db_session.commit()

    found_user = await repository.get_by_github_id(99)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.username == "hubot"


async def test_get_by_id_returns_none_for_missing_user(
    repository: UserRepository,
) -> None:
    """Repository should return None when a user does not exist."""
    user = await repository.get_by_id(999)

    assert user is None


async def test_list_all_returns_users_in_creation_order(
    repository: UserRepository,
    db_session: AsyncSession,
) -> None:
    """Repository should return all users ordered by creation time."""
    first_user = await repository.create(github_id=1, username="first")
    second_user = await repository.create(github_id=2, username="second")
    await db_session.commit()

    users = await repository.list_all()

    assert len(users) == 2
    assert users[0].id == first_user.id
    assert users[1].id == second_user.id


async def test_delete_removes_user(
    repository: UserRepository,
    db_session: AsyncSession,
) -> None:
    """Deleting a user should remove it from the database."""
    user = await repository.create(github_id=42, username="delete-me")
    await db_session.commit()

    await repository.delete(user)
    await db_session.commit()

    assert await repository.get_by_id(user.id) is None
