from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_order_and_audit_api_flow(client: AsyncClient) -> None:
    """Test full HTTP API flow for Order Management and Audit Trail."""
    # 1. Onboard merchant & product
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Audit API Sweets", "type": "local_merchant", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Kaju Roll",
            "category": "sweets",
            "price_amount": 55000,  # ₹550
            "quantity": 10,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )
    product_id = p_res.json()["product_id"]

    user_id = "user-api-audit-1"

    # 2. Create Order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        json={"user_id": user_id, "product_id": product_id, "quantity": 1},
    )
    order_id = order_res.json()["order_id"]

    # 3. Get Order Details via GET /api/v1/orders/{id}
    get_res = await client.get(f"/api/v1/orders/{order_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["order_id"] == order_id
    assert data["product_name"] == "Kaju Roll"
    assert data["merchant_name"] == "Audit API Sweets"

    # 4. List User Orders via GET /api/v1/orders/users/{user_id}
    user_orders_res = await client.get(f"/api/v1/orders/users/{user_id}")
    assert user_orders_res.status_code == 200
    assert len(user_orders_res.json()) >= 1

    # 5. Merchant updates status via POST /api/v1/orders/{order_id}/status
    status_update_res = await client.post(
        f"/api/v1/orders/{order_id}/status",
        json={"merchant_id": merchant_id, "status": "ready_for_pickup"},
    )
    assert status_update_res.status_code == 200
    assert status_update_res.json()["status"] == "ready_for_pickup"

    # 6. Fetch Order Audit Timeline via GET /api/v1/orders/{order_id}/timeline
    timeline_res = await client.get(f"/api/v1/orders/{order_id}/timeline")
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()
    assert timeline_data["order_id"] == order_id
    assert timeline_data["total_events"] >= 1

    # 7. Query Global Audit Events via GET /api/v1/audit/events
    audit_res = await client.get(f"/api/v1/audit/events?order_id={order_id}")
    assert audit_res.status_code == 200
    events = audit_res.json()
    assert len(events) >= 1
