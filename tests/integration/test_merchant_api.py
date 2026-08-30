from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_get_merchant_api(client: AsyncClient) -> None:
    """Test POST /api/v1/merchants/ and GET /api/v1/merchants/{id}."""
    payload = {
        "name": "Aggarwal Sweets",
        "type": "local_merchant",
        "description": "Authentic North Indian Sweets",
        "location": "Karol Bagh, Delhi",
        "pincode": "110005",
    }
    
    # 1. Register merchant
    response = await client.post("/api/v1/merchants/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aggarwal Sweets"
    assert data["type"] == "local_merchant"
    assert "provider_id" in data
    merchant_id = data["provider_id"]

    # 2. Get merchant by ID
    get_res = await client.get(f"/api/v1/merchants/{merchant_id}")
    assert get_res.status_code == 200
    assert get_res.json()["provider_id"] == merchant_id
    assert get_res.json()["name"] == "Aggarwal Sweets"


@pytest.mark.asyncio
async def test_list_merchants_api(client: AsyncClient) -> None:
    """Test GET /api/v1/merchants/."""
    response = await client.get("/api/v1/merchants/")
    assert response.status_code == 200
    merchants = response.json()
    assert isinstance(merchants, list)
    # Seed merchants or newly registered should be present
    assert len(merchants) >= 1


@pytest.mark.asyncio
async def test_get_nonexistent_merchant_api(client: AsyncClient) -> None:
    """Test GET /api/v1/merchants/{id} with invalid ID."""
    response = await client.get("/api/v1/merchants/non-existent-id")
    assert response.status_code in (400, 404)
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
