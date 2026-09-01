from __future__ import annotations

from typing import TYPE_CHECKING
from app.mcp.tools import MCP_TOOLS_DEFINITIONS, MCPCommerceTools

if TYPE_CHECKING:
    from app.mcp.server import MCPServer

__all__ = ["MCPServer", "MCPCommerceTools", "MCP_TOOLS_DEFINITIONS"]


def __getattr__(name: str) -> object:
    if name == "MCPServer":
        from app.mcp.server import MCPServer
        return MCPServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
