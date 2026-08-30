from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_global_manifest_api(client: AsyncClient) -> None:
    """Test GET /api/v1/manifest.json and /api/v1/manifests."""
    response = await client.get("/api/v1/manifest.json")
    assert response.status_code == 200
    data = response.json()
    assert "manifest_version" in data
    assert "total_merchants" in data
    assert "merchants" in data
    assert isinstance(data["merchants"], list)

    # Test alias /api/v1/manifests
    alias_response = await client.get("/api/v1/manifests")
    assert alias_response.status_code == 200
    assert alias_response.json()["total_merchants"] == data["total_merchants"]


@pytest.mark.asyncio
async def test_merchant_manifest_and_jsonld_api(client: AsyncClient) -> None:
    """Test GET /api/v1/merchants/{id}/manifest.json and schema.jsonld."""
    # 1. Create merchant
    m_res = await client.post(
        "/api/v1/merchants/",
        json={
            "name": "Evergreen Sweet House",
            "type": "local_merchant",
            "location": "Green Park, Delhi",
            "pincode": "110016",
        },
    )
    assert m_res.status_code == 201
    merchant_id = m_res.json()["provider_id"]

    # 2. Add product
    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Motichoor Ladoo",
            "description": "Fine pearl gram flour sweet balls in pure ghee",
            "category": "sweets",
            "price_amount": 55000,  # ₹550
            "price_currency": "INR",
            "quantity": 40,
            "availability_status": "in_stock",
            "fulfillment_type": "pickup",
            "prep_time_minutes": 10,
            "pincode": "110016",
        },
    )
    assert p_res.status_code == 201

    # 3. Get Merchant Manifest
    manifest_res = await client.get(f"/api/v1/merchants/{merchant_id}/manifest.json")
    assert manifest_res.status_code == 200
    manifest_data = manifest_res.json()
    assert manifest_data["provider_id"] == merchant_id
    assert manifest_data["name"] == "Evergreen Sweet House"
    assert manifest_data["capabilities"]["can_pickup"] is True
    assert "110016" in manifest_data["capabilities"]["delivery_pincodes"]
    assert len(manifest_data["categories"]) == 1
    assert manifest_data["categories"][0]["category"] == "sweets"
    assert manifest_data["categories"][0]["min_price_amount"] == 55000
    assert len(manifest_data["available_tools"]) >= 2

    # 4. Get Schema.org JSON-LD
    jsonld_res = await client.get(f"/api/v1/merchants/{merchant_id}/schema.jsonld")
    assert jsonld_res.status_code == 200
    jsonld_data = jsonld_res.json()
    assert jsonld_data["@context"] == "https://schema.org"
    assert jsonld_data["@type"] == "Store"
    assert jsonld_data["name"] == "Evergreen Sweet House"
    assert "hasOfferCatalog" in jsonld_data
