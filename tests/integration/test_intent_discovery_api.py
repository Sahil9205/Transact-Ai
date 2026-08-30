from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_intent_parse_api(client: AsyncClient) -> None:
    """Test POST /api/v1/intent/parse."""
    response = await client.post(
        "/api/v1/intent/parse",
        json={"prompt": "1kg rasgulla under ₹500 by 6:30 PM in 110001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "rasgulla" in data["product_query"].lower()
    assert data["max_price"] == 50000
    assert data["deadline"] == "6:30 PM"
    assert data["category"] == "sweets"
    assert data["pincode"] == "110001"


@pytest.mark.asyncio
async def test_discovery_match_api_with_prompt(client: AsyncClient) -> None:
    """Test POST /api/v1/discovery/match with natural language prompt."""
    # 1. Onboard merchant & product
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Discovery Sweet Hub", "type": "local_merchant", "pincode": "110001"},
    )
    assert m_res.status_code == 201
    merchant_id = m_res.json()["provider_id"]

    await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Kesari Rasgulla",
            "category": "sweets",
            "price_amount": 42000,  # ₹420
            "quantity": 25,
            "availability_status": "in_stock",
            "fulfillment_type": "pickup",
            "prep_time_minutes": 15,
            "pincode": "110001",
        },
    )

    # 2. Run discovery match with prompt
    match_res = await client.post(
        "/api/v1/discovery/match",
        json={"prompt": "Kesari Rasgulla under 500 in 110001"},
    )
    assert match_res.status_code == 200
    data = match_res.json()
    assert data["total_candidates"] >= 1
    assert data["parsed_intent"]["max_price"] == 50000
    assert any(c["product"]["name"] == "Kesari Rasgulla" for c in data["candidates"])
    assert data["candidates"][0]["price_inr"] <= 500.0


@pytest.mark.asyncio
async def test_discovery_match_api_budget_rejection(client: AsyncClient) -> None:
    """Test discovery match strictly filters out items exceeding budget."""
    match_res = await client.post(
        "/api/v1/discovery/match",
        json={"prompt": "Rasgulla under 200 in 110001"},  # Too low for ₹450 Rasgulla
    )
    assert match_res.status_code == 200
    data = match_res.json()
    # All candidates returned MUST be <= ₹200 (20000 paise)
    for c in data["candidates"]:
        assert c["product"]["pricing"]["amount"] <= 20000
