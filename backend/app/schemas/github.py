"""GitHub API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class GitHubUserProfile(BaseModel):
    """Normalized GitHub user profile used during OAuth."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(gt=0)
    login: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)
