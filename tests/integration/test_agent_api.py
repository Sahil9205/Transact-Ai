from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agent_chat_api_success_flow(client: AsyncClient) -> None:
    """Test POST /api/v1/agent/chat and POST /api/v1/agent/confirm."""
    # 1. Onboard merchant & product @ ₹450
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "API Sweets", "type": "local_merchant", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    p_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Gulab Jamun Plate",
            "category": "sweets",
            "price_amount": 35000,  # ₹350
            "quantity": 30,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )
    product_id = p_res.json()["product_id"]

    user_id = "buyer-agent-api-1"

    # 2. Chat with agent
    chat_res = await client.post(
        "/api/v1/agent/chat",
        json={
            "user_id": user_id,
            "prompt": "1 plate Gulab Jamun chahiye under ₹400 in 110001",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["status"] == "proposed"
    assert chat_data["order_proposal"] is not None
    assert chat_data["order_proposal"]["product_name"] == "Gulab Jamun Plate"
    assert chat_data["order_proposal"]["total_amount_inr"] == 350.0
    assert "Found the best option!" in chat_data["agent_message"]

    # 3. Confirm order proposal
    confirm_res = await client.post(
        "/api/v1/agent/confirm",
        json={
            "user_id": user_id,
            "product_id": product_id,
            "total_amount_paise": 35000,
            "confirmed": True,
        },
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["confirmed"] is True
    assert confirm_data["status"] == "payment_ready"
