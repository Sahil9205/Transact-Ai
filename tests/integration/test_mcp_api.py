from __future__ import annotations

import json
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mcp_tools_discovery_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/mcp/tools REST endpoint."""
    response = await client.get("/api/v1/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) >= 5


@pytest.mark.asyncio
async def test_mcp_jsonrpc_lifecycle(client: AsyncClient) -> None:
    """Test MCP JSON-RPC protocol lifecycle over HTTP."""
    # 1. Initialize method
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    init_res = await client.post("/api/v1/mcp/rpc", json=init_payload)
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["jsonrpc"] == "2.0"
    assert init_data["id"] == 1
    assert init_data["result"]["serverInfo"]["name"] == "transact-ai-mcp"

    # 2. tools/list method
    list_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }
    list_res = await client.post("/api/v1/mcp/rpc", json=list_payload)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "tools" in list_data["result"]
    assert len(list_data["result"]["tools"]) >= 5

    # 3. tools/call method (search catalog)
    call_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "transact_search_catalog",
            "arguments": {
                "query": "Rasgulla",
                "max_price_inr": 500,
            },
        },
    }
    call_res = await client.post("/api/v1/mcp/rpc", json=call_payload)
    assert call_res.status_code == 200
    call_data = call_res.json()
    assert call_data["id"] == 3
    assert "content" in call_data["result"]
    assert len(call_data["result"]["content"]) >= 1
    content_text = call_data["result"]["content"][0]["text"]
    parsed_content = json.loads(content_text)
    assert "total_matches" in parsed_content

    # 4. Unknown method error response
    bad_payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "unknown_method",
    }
    bad_res = await client.post("/api/v1/mcp/rpc", json=bad_payload)
    assert bad_res.status_code == 200
    bad_data = bad_res.json()
    assert "error" in bad_data
    assert bad_data["error"]["code"] == -32601
