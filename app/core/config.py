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
    
    # Qdrant Vector DB
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "products"
    
    # LangSmith / LangChain Tracing
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "transact-ai"
    LANGCHAIN_TRACING_V2: bool = True
    
    # Razorpay Payment Gateway (Test Mode default)
    RAZORPAY_KEY_ID: str = "rzp_test_mock_transact_ai"
    RAZORPAY_KEY_SECRET: str = "mock_secret_key_123456"
    RAZORPAY_WEBHOOK_SECRET: str = "mock_webhook_secret_123456"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def DEBUG(self) -> bool:
        """Computed property indicating debug mode based on APP_ENV."""
        return self.APP_ENV.lower() == "development"


@functools.lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
