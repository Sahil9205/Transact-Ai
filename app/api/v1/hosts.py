from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.agent_service import AgentService
from app.services.external_host_service import ExternalHostService

router = APIRouter(prefix="/hosts", tags=["External AI Host Connectors"])


class ExecuteToolRequest(BaseModel):
    """Payload to execute a specific tool call on behalf of an external AI host."""
    tool_name: str = Field(..., examples=["search_products"], description="Canonical name of tool to invoke")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary matching tool schema")
    user_id: str = Field(default="host_user_1", description="ID of buyer/user driving the conversation")


class HostChatRequest(BaseModel):
    """Payload for external AI host to initiate an autonomous commerce session."""
    prompt: str = Field(..., examples=["1kg Rasgulla under ₹500 in 110001"], description="User prompt")
    user_id: str = Field(default="external_host_user", description="Buyer user ID")
    host: str = Field(default="generic", examples=["gemini", "openai", "claude", "custom_copilot"])


@router.get(
    "/tools",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Export Host-Native Tool Definitions",
    description="Returns all Transact AI commerce tools formatted natively for Google Gemini (functionDeclarations), OpenAI ChatGPT (tools), or Anthropic Claude (input_schema).",
)
async def get_host_tools_endpoint(
    format: str = Query(default="openai", description="Target host format: 'gemini', 'openai', or 'anthropic'"),
) -> list[dict[str, Any]]:
    """Export tool schemas for external AI hosts."""
    return ExternalHostService.get_host_tools_schema(format=format)


@router.post(
    "/execute-tool",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Universal Tool Execution Proxy",
    description="Allows external agents (Gemini, Claude, GPT) to dispatch tool calls directly to Transact AI core with live DB validation.",
)
async def execute_tool_endpoint(
    payload: ExecuteToolRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute a tool call from an external AI host."""
    return await ExternalHostService.dispatch_tool_call(
        session=session,
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        user_id=payload.user_id,
    )


@router.post(
    "/chat-connector",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Host Commerce Chat Connector",
    description="End-to-end autonomous session connector for external host copilots.",
)
async def host_chat_connector_endpoint(
    payload: HostChatRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run full commerce orchestration and return standardized host package."""
    final_state = await AgentService.run_agent(
        session=session,
        user_id=payload.user_id,
        prompt=payload.prompt,
    )

    return {
        "host": payload.host,
        "user_id": payload.user_id,
        "status": final_state["status"],
        "agent_message": final_state["agent_message"],
        "proposal": final_state["order_proposal"].model_dump(mode="json") if final_state["order_proposal"] else None,
        "alternatives": [a.model_dump(mode="json") for a in final_state.get("alternatives", [])],
        "step_history": final_state["step_history"],
    }
