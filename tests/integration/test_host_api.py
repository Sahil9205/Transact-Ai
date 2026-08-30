from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_host_tools_export_and_execution_endpoints(client: AsyncClient) -> None:
    """Test host tools export and tool execution proxy endpoints."""
    # 1. Test GET /api/v1/hosts/tools for all 3 formats
    for fmt in ["gemini", "openai", "anthropic"]:
        res = await client.get(f"/api/v1/hosts/tools?format={fmt}")
        assert res.status_code == 200
        tools = res.json()
        assert len(tools) == 6

    # 2. Onboard merchant & product
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "API Host Merchant", "type": "local_merchant", "pincode": "110001"},
    )
    merchant_id = m_res.json()["provider_id"]

    await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Host API Sandesh",
            "category": "sweets",
            "price_amount": 30000,
            "quantity": 10,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )

    # 3. Test POST /api/v1/hosts/execute-tool (search_products)
    exec_res = await client.post(
        "/api/v1/hosts/execute-tool",
        json={
            "tool_name": "search_products",
            "arguments": {"query": "Sandesh", "pincode": "110001"},
            "user_id": "gemini_copilot_user",
        },
    )
    assert exec_res.status_code == 200
    data = exec_res.json()
    assert data["success"] is True
    assert data["total_matches"] >= 1

    # 4. Test POST /api/v1/hosts/chat-connector
    chat_res = await client.post(
        "/api/v1/hosts/chat-connector",
        json={
            "prompt": "Sandesh in 110001",
            "user_id": "claude_user",
            "host": "claude",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["host"] == "claude"
    assert "agent_message" in chat_data
