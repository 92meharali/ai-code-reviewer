"""User API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Payload for creating a user."""

    github_id: int = Field(gt=0)
    username: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)


class UserRead(BaseModel):
    """User data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    github_id: int
    username: str
    email: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
