from __future__ import annotations

import hashlib
import hmac
import pytest
from httpx import AsyncClient

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_e2e_happy_path_scenario(client: AsyncClient) -> None:
    """E2E Test: Natural Language Prompt -> Proposal -> Razorpay Order -> Signature Settlement -> Timeline."""
    settings = get_settings()

    # 1. Onboard Merchant & Product
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "E2E Sharma Sweets", "type": "local_merchant", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "E2E Fresh Rasgulla",
            "category": "sweets",
            "price_amount": 45000,  # ₹450
            "quantity": 25,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )
    product_id = p_res.json()["product_id"]

    user_id = "e2e_shopper_1"

    # 2. Agent Chat API Call
    chat_res = await client.post(
        "/api/v1/agent/chat",
        json={"user_id": user_id, "prompt": "1kg Rasgulla under 500 in 110001"},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["status"] == "proposed"
    proposal = chat_data["order_proposal"]
    assert proposal["unit_price_inr"] == 450.0

    # 3. Create Payment Order
    pay_res = await client.post(
        "/api/v1/payments/create-order",
        json={"user_id": user_id, "product_id": proposal["product_id"], "quantity": 1},
    )
    assert pay_res.status_code == 201
    pay_data = pay_res.json()
    order_id = pay_data["order_id"]
    rzp_order_id = pay_data["razorpay_order_id"]

    # 4. Cryptographic HMAC Signature Settlement
    mock_pay_id = "pay_rzp_mock_e2e_999"
    msg = f"{rzp_order_id}|{mock_pay_id}".encode("utf-8")
    sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    verify_res = await client.post(
        "/api/v1/payments/verify-signature",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": mock_pay_id,
            "razorpay_signature": sig,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True
    assert verify_res.json()["status"] == "order_created"

    # 5. Check 3-Layer Audit Timeline
    timeline_res = await client.get(f"/api/v1/orders/{order_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert timeline["total_events"] >= 3
    event_types = [e["event_type"] for e in timeline["timeline"]]
    assert "payment_initiated" in event_types
    assert "payment_success" in event_types
    assert "order_created" in event_types


@pytest.mark.asyncio
async def test_e2e_recipe_to_purchase_connector(client: AsyncClient) -> None:
    """E2E Test: External AI Host connector executing multi-provider comparison and order."""
    # 1. Onboard Blinkit Dark Store
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Blinkit Quick Dark Store", "type": "enterprise", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Nescafe Classic 100g Jar",
            "category": "groceries",
            "price_amount": 29000,  # ₹290
            "quantity": 30,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )
    product_id = p_res.json()["product_id"]

    # 2. Host invokes execute-tool: search_products
    tool_search = await client.post(
        "/api/v1/hosts/execute-tool",
        json={
            "tool_name": "search_products",
            "arguments": {"query": "Nescafe", "pincode": "110001"},
            "user_id": "chatgpt_user",
        },
    )
    assert tool_search.status_code == 200
    assert tool_search.json()["total_matches"] >= 1

    # 3. Host invokes execute-tool: verify_order_preflight
    tool_verify = await client.post(
        "/api/v1/hosts/execute-tool",
        json={
            "tool_name": "verify_order_preflight",
            "arguments": {"user_id": "chatgpt_user", "product_id": product_id, "quantity": 1},
            "user_id": "chatgpt_user",
        },
    )
    assert tool_verify.status_code == 200
    assert tool_verify.json()["gatekeeper_decision"]["is_authorized"] is True
