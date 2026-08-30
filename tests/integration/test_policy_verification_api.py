from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_policy_management_api(client: AsyncClient) -> None:
    """Test POST /api/v1/policies/users/{id} and GET /api/v1/policies/users/{id}."""
    user_id = "user-api-policy-1"

    # 1. Configure policy
    post_res = await client.post(
        f"/api/v1/policies/users/{user_id}",
        json={
            "max_per_transaction_inr": 1500.0,
            "daily_limit_inr": 4000.0,
            "allowed_categories": ["sweets", "food"],
            "is_active": True,
        },
    )
    assert post_res.status_code == 200
    policy_data = post_res.json()
    assert policy_data["user_id"] == user_id
    assert policy_data["max_per_transaction"] == 150000
    assert policy_data["daily_limit"] == 400000

    # 2. Get policy status and budget tracker
    get_res = await client.get(f"/api/v1/policies/users/{user_id}")
    assert get_res.status_code == 200
    status_data = get_res.json()
    assert status_data["policy"]["user_id"] == user_id
    assert status_data["spent_today_inr"] == 0.0
    assert status_data["remaining_daily_budget_inr"] == 4000.0


@pytest.mark.asyncio
async def test_preflight_verification_api_allow_and_block(client: AsyncClient) -> None:
    """Test POST /api/v1/verification/preflight for ALLOW and BLOCK scenarios."""
    # 1. Register merchant & add product @ ₹450
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Preflight Sweets", "type": "local_merchant", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Special Rasgulla Tin",
            "category": "sweets",
            "price_amount": 45000,  # ₹450
            "quantity": 10,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )
    product_id = p_res.json()["product_id"]

    # 2. Configure user policy with max ₹1000 per tx
    user_id = "user-preflight-test"
    await client.post(
        f"/api/v1/policies/users/{user_id}",
        json={
            "max_per_transaction_inr": 1000.0,
            "daily_limit_inr": 2000.0,
        },
    )

    # 3. Preflight check: 1 unit @ ₹450 -> should be ALLOWED
    allow_res = await client.post(
        "/api/v1/verification/preflight",
        json={
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 1,
        },
    )
    assert allow_res.status_code == 200
    allow_data = allow_res.json()
    assert allow_data["is_authorized"] is True
    assert allow_data["decision"] == "ALLOW"
    assert allow_data["total_amount_inr"] == 450.0

    # 4. Preflight check: 3 units @ ₹450 = ₹1350 > ₹1000 max tx limit -> should be BLOCKED
    block_res = await client.post(
        "/api/v1/verification/preflight",
        json={
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 3,
        },
    )
    assert block_res.status_code == 200
    block_data = block_res.json()
    assert block_data["is_authorized"] is False
    assert block_data["decision"] == "BLOCK"
    assert any("per_transaction_limit_exceeded" in r for r in block_data["blocked_reasons"])
