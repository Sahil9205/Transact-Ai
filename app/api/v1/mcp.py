from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.mcp.server import MCPServer
from app.mcp.tools import MCP_TOOLS_DEFINITIONS

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])


@router.post(
    "/rpc",
    summary="MCP JSON-RPC Endpoint",
    description="Standard JSON-RPC 2.0 endpoint implementing Model Context Protocol methods (initialize, tools/list, tools/call).",
)
async def mcp_jsonrpc_endpoint(
    request_body: dict[str, Any] = Body(
        ...,
        examples=[
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "transact_search_catalog",
                    "arguments": {"query": "rasgulla", "max_price_inr": 500},
                },
            },
        ],
    ),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute standard MCP JSON-RPC 2.0 request."""
    return await MCPServer.handle_request(session, request_body)


@router.get(
    "/tools",
    summary="List Available MCP Tools",
    description="Returns the array of available MCP tool definitions and JSON schemas.",
)
async def list_mcp_tools() -> dict[str, Any]:
    """List all registered MCP commerce tools."""
    return {
        "tools": MCP_TOOLS_DEFINITIONS,
    }


@router.get(
    "/sse",
    summary="MCP Server-Sent Events (SSE) Stream",
    description="Provides an SSE connection for web-based MCP client transports.",
)
async def mcp_sse_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Server-Sent Events endpoint for MCP protocol streaming."""

    async def event_generator() -> AsyncGenerator[str, None]:
        # Emit initial endpoint declaration
        initial_payload = {
            "jsonrpc": "2.0",
            "method": "endpoint",
            "params": {"endpoint": "/api/v1/mcp/rpc"},
        }
        yield f"event: endpoint\ndata: {json.dumps(initial_payload)}\n\n"

        # Keep alive heartbeat
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(15)
            yield f"event: ping\ndata: {json.dumps({'type': 'ping'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
