"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "AI Code Reviewer"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
