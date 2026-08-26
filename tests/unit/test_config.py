from __future__ import annotations

import pytest
from app.core.config import Settings

def test_default_settings() -> None:
    """Test that Settings loads with correct default values."""
    # Use _env_file=None to prevent .env from overriding defaults
    settings = Settings(_env_file=None)
    assert settings.APP_ENV == "development"
    assert settings.APP_NAME == "transact-ai"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///./data/commerce.db"
    assert settings.DEBUG is True

def test_settings_debug_mode() -> None:
    """Test that DEBUG mode is correctly computed."""
    dev_settings = Settings(APP_ENV="development", _env_file=None)
    assert dev_settings.DEBUG is True
    
    prod_settings = Settings(APP_ENV="production", _env_file=None)
    assert prod_settings.DEBUG is False

def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Settings values can be overridden via environment variables."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_VERSION", "1.0.0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    
    settings = Settings()
    assert settings.APP_ENV == "production"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"
    assert settings.DEBUG is False
