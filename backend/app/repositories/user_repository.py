"""User data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for user persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        github_id: int,
        username: str,
        email: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Create and persist a new user."""
        user = User(
            github_id=github_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        """Return a user by primary key."""
        return await self._session.get(User, user_id)

    async def get_by_github_id(self, github_id: int) -> User | None:
        """Return a user by GitHub ID."""
        result = await self._session.execute(
            select(User).where(User.github_id == github_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        """Return all users ordered by creation time."""
        result = await self._session.execute(
            select(User).order_by(User.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, user: User) -> None:
        """Delete a user record."""
        await self._session.delete(user)
        await self._session.flush()
