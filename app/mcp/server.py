from __future__ import annotations

import asyncio
import json
import sys
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import init_database_manager
from app.mcp.tools import MCP_TOOLS_DEFINITIONS, MCPCommerceTools

logger = get_logger(__name__)

MCP_SERVER_INFO = {
    "name": "transact-ai-mcp",
    "version": "0.1.0",
}


class MCPServer:
    """Model Context Protocol (MCP) JSON-RPC Server for Transact AI."""

    @staticmethod
    async def handle_request(session: AsyncSession, request: dict[str, Any]) -> dict[str, Any]:
        """Processes a standard MCP JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        logger.debug("Received MCP request", method=method, req_id=req_id)

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": MCP_SERVER_INFO,
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                }
            elif method == "tools/list":
                result = {
                    "tools": MCP_TOOLS_DEFINITIONS,
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                tool_result = await MCPServer._dispatch_tool(session, tool_name, arguments)
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tool_result, indent=2),
                        }
                    ],
                    "isError": False,
                }
            elif method in ["notifications/initialized", "initialized"]:
                return None
            elif method == "ping":
                result = {}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            }

        except Exception as e:
            logger.error("MCP tool execution error", method=method, error=str(e))
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": str(e),
                },
            }

    @staticmethod
    async def _dispatch_tool(session: AsyncSession, tool_name: str | None, args: dict[str, Any]) -> Any:
        """Dispatches tool execution to the appropriate handler."""
        if tool_name == "transact_discover_merchants":
            return await MCPCommerceTools.discover_merchants(
                session=session,
                pincode=args.get("pincode"),
                category=args.get("category"),
            )
        elif tool_name == "transact_search_catalog":
            return await MCPCommerceTools.search_catalog(
                session=session,
                query=args.get("query", ""),
                category=args.get("category"),
                max_price_inr=args.get("max_price_inr"),
                pincode=args.get("pincode"),
                merchant_id=args.get("merchant_id"),
            )
        elif tool_name == "transact_get_product":
            return await MCPCommerceTools.get_product(
                session=session,
                product_id=args.get("product_id", ""),
            )
        elif tool_name == "transact_check_availability":
            return await MCPCommerceTools.check_availability(
                session=session,
                product_id=args.get("product_id", ""),
            )
        elif tool_name == "transact_get_merchant_manifest":
            return await MCPCommerceTools.get_merchant_manifest(
                session=session,
                merchant_id=args.get("merchant_id", ""),
            )
        else:
            raise ValueError(f"Unknown MCP tool: '{tool_name}'")


async def run_stdio_server() -> None:
    """Runs the MCP server over standard input/output (stdio) for desktop AI hosts."""
    from app.core.logging import setup_logging
    # Send all logging to stderr so stdout is strictly JSON-RPC messages
    setup_logging(log_level="INFO", environment="development", stream=sys.stderr)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    settings = get_settings()
    db_manager = init_database_manager(settings.DATABASE_URL)
    await db_manager.init_db()

    sys.stderr.write("Transact AI MCP Server running on stdio for Claude Desktop...\n")
    sys.stderr.flush()

    loop = asyncio.get_event_loop()

    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            line_str = line.strip()
            if not line_str:
                continue

            request = json.loads(line_str)
            req_id = request.get("id")
            method = request.get("method")

            # Skip notifications where response is not expected
            if req_id is None and method and method.startswith("notifications/"):
                continue

            async for session in db_manager.get_session():
                response = await MCPServer.handle_request(session, request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                break
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"stdio MCP error: {e}\n")
            sys.stderr.flush()

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_stdio_server())
