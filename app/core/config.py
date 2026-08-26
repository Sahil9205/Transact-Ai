from __future__ import annotations

import functools
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    APP_ENV: str = "development"
    APP_NAME: str = "transact-ai"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/commerce.db"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def DEBUG(self) -> bool:
        """Computed property indicating debug mode based on APP_ENV."""
        return self.APP_ENV.lower() == "development"


@functools.lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
