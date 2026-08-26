from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_health_endpoint(client: AsyncClient) -> None:
    """Test the basic health check endpoint."""
    response = await client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data

async def test_readiness_endpoint(client: AsyncClient) -> None:
    """Test the readiness check endpoint."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data

async def test_root_endpoint(client: AsyncClient) -> None:
    """Test the root endpoint redirects."""
    response = await client.get("/", follow_redirects=False)
    # RedirectResponse uses 307 by default in FastAPI
    assert response.status_code in (302, 307)
    assert "/docs" in response.headers["location"]
