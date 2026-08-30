from __future__ import annotations

import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_payment_api_complete_lifecycle(client: AsyncClient) -> None:
    """Test full payment lifecycle over HTTP REST endpoints."""
    settings = get_settings()

    # 1. Onboard merchant & product
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Payment Test Sweet Shop", "type": "local_merchant", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Chhena Murki",
            "category": "sweets",
            "price_amount": 25000,  # ₹250
            "quantity": 10,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )
    product_id = p_res.json()["product_id"]

    # 2. Create Payment Order via POST /api/v1/payments/create-order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        json={
            "user_id": "buyer-api-pay-1",
            "product_id": product_id,
            "quantity": 2,
        },
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["amount_inr"] == 500.0
    assert order_data["amount_paise"] == 50000
    assert order_data["status"] == "payment_pending"
    razorpay_order_id = order_data["razorpay_order_id"]
    internal_order_id = order_data["order_id"]

    # 3. Verify Signature via POST /api/v1/payments/verify-signature
    mock_pay_id = "pay_api_mock_999"
    msg = f"{razorpay_order_id}|{mock_pay_id}".encode("utf-8")
    valid_sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    verify_res = await client.post(
        "/api/v1/payments/verify-signature",
        json={
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": mock_pay_id,
            "razorpay_signature": valid_sig,
        },
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["status"] == "order_created"

    # 4. Check Order Status via GET /api/v1/payments/orders/{id}
    status_res = await client.get(f"/api/v1/payments/orders/{internal_order_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["order_id"] == internal_order_id
    assert status_data["status"] == "order_created"
    assert status_data["payment_status"] == "success"


@pytest.mark.asyncio
async def test_payment_webhook_endpoint(client: AsyncClient) -> None:
    """Test POST /api/v1/payments/webhook."""
    settings = get_settings()

    # 1. Onboard & create order
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Webhook Sweets", "type": "local_merchant"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Peda Box",
            "category": "sweets",
            "price_amount": 30000,
            "quantity": 10,
        },
    )
    product_id = p_res.json()["product_id"]

    order_res = await client.post(
        "/api/v1/payments/create-order",
        json={"user_id": "buyer-hook-user", "product_id": product_id, "quantity": 1},
    )
    razorpay_order_id = order_res.json()["razorpay_order_id"]

    # 2. Fire Webhook
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_hook_987",
                    "order_id": razorpay_order_id,
                    "amount": 30000,
                    "status": "captured",
                }
            }
        },
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    hook_res = await client.post(
        "/api/v1/payments/webhook",
        content=body_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
    )
    assert hook_res.status_code == 200
    hook_data = hook_res.json()
    assert hook_data["processed"] is True
