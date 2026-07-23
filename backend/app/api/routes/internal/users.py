"""Internal user CRUD routes for development and testing."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["internal-users"])


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    """Provide a user repository bound to the request session."""
    return UserRepository(session)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    repository: UserRepository = Depends(get_user_repository),
) -> UserRead:
    """Create a new user."""
    existing_user = await repository.get_by_github_id(payload.github_id)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this GitHub ID already exists",
        )

    user = await repository.create(
        github_id=payload.github_id,
        username=payload.username,
        email=payload.email,
        avatar_url=payload.avatar_url,
    )
    return UserRead.model_validate(user)


@router.get("", response_model=list[UserRead])
async def list_users(
    repository: UserRepository = Depends(get_user_repository),
) -> list[UserRead]:
    """List all users."""
    users = await repository.list_all()
    return [UserRead.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    repository: UserRepository = Depends(get_user_repository),
) -> UserRead:
    """Return a user by ID."""
    user = await repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    repository: UserRepository = Depends(get_user_repository),
) -> None:
    """Delete a user by ID."""
    user = await repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await repository.delete(user)
