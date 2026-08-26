from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

from app.core.config import Settings, get_settings
from app.main import create_app
from fastapi import FastAPI

@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings with SQLite test database."""
    return Settings(DATABASE_URL="sqlite+aiosqlite:///./data/test.db", APP_ENV="testing")

@pytest.fixture
async def app(test_settings: Settings) -> AsyncGenerator[FastAPI, None]:
    """Create a FastAPI application instance for testing."""
    test_app = create_app()
    test_app.dependency_overrides[get_settings] = lambda: test_settings
    
    async with test_app.router.lifespan_context(test_app):
        yield test_app

@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient for testing the app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
