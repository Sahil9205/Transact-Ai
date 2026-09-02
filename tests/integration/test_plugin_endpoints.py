from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chatgpt_plugin_manifest_endpoint(client: AsyncClient) -> None:
    """Test standard ChatGPT plugin manifest endpoint."""
    res = await client.get("/.well-known/ai-plugin.json")
    assert res.status_code == 200
    data = res.json()
    assert data["name_for_model"] == "transact_ai"
    assert data["schema_version"] == "v1"
    assert data["auth"]["type"] == "none"


@pytest.mark.asyncio
async def test_chatgpt_plugin_openapi_endpoint(client: AsyncClient) -> None:
    """Test ChatGPT Custom Action OpenAPI spec endpoint."""
    res = await client.get("/.well-known/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert data["openapi"] == "3.1.0"
    assert "/api/v1/hosts/execute-tool" in data["paths"]


@pytest.mark.asyncio
async def test_gemini_extension_manifest_endpoint(client: AsyncClient) -> None:
    """Test Google Gemini extension manifest endpoint."""
    res = await client.get("/.well-known/gemini-extension.json")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "transact_ai"
    assert len(data["tools"]) >= 4


@pytest.mark.asyncio
async def test_remote_mcp_http_endpoints(client: AsyncClient) -> None:
    """Test remote Claude Streamable HTTP / JSON-RPC endpoints on /mcp."""
    # 1. Test tools list endpoint
    tools_res = await client.get("/mcp/tools")
    assert tools_res.status_code == 200
    tools_data = tools_res.json()
    assert "tools" in tools_data
    assert len(tools_data["tools"]) >= 4

    # 2. Test JSON-RPC initialize handshake on root /mcp
    rpc_res = await client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        },
    )
    assert rpc_res.status_code == 200
    rpc_data = rpc_res.json()
    assert rpc_data["jsonrpc"] == "2.0"
    assert rpc_data["id"] == 1
    assert "result" in rpc_data
    assert "tools" in rpc_data["result"]

    # 3. Test notifications/initialized (which previously caused 500 error)
    notify_res = await client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        },
    )
    assert notify_res.status_code == 200
    notify_data = notify_res.json()
    assert notify_data["jsonrpc"] == "2.0"


