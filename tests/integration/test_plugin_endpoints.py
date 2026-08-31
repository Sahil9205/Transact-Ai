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
