from __future__ import annotations

from typing import Any
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.nodes import (
    node_create_proposal,
    node_discover_candidates,
    node_handle_failure,
    node_parse_intent,
    node_verify_and_gatekeep,
)
from app.agent.state import CommerceAgentState
from app.core.logging import get_logger
from app.services.vector_service import VectorService

logger = get_logger(__name__)


def route_after_discovery(state: CommerceAgentState) -> str:
    """Routes to gatekeeper if candidates were discovered, else failure node."""
    candidates = state.get("candidates", [])
    if candidates and len(candidates) > 0:
        return "verify_and_gatekeep"
    return "handle_failure"


def route_after_gatekeeper(state: CommerceAgentState) -> str:
    """Routes to proposal creation if gatekeeper approved, else failure node."""
    decision = state.get("gatekeeper_decision")
    if decision and decision.is_authorized:
        return "create_proposal"
    return "handle_failure"


def build_commerce_agent_graph(
    session: AsyncSession,
    vector_service: VectorService | None = None,
) -> Any:
    """Constructs and compiles the deterministic LangGraph commerce workflow."""
    workflow = StateGraph(CommerceAgentState)

    # Node wrappers passing session & vector_service
    async def _parse_intent(state: CommerceAgentState) -> dict[str, Any]:
        return await node_parse_intent(state, session)

    async def _discover_candidates(state: CommerceAgentState) -> dict[str, Any]:
        return await node_discover_candidates(state, session, vector_service)

    async def _verify_and_gatekeep(state: CommerceAgentState) -> dict[str, Any]:
        return await node_verify_and_gatekeep(state, session)

    async def _create_proposal(state: CommerceAgentState) -> dict[str, Any]:
        return await node_create_proposal(state, session)

    async def _handle_failure(state: CommerceAgentState) -> dict[str, Any]:
        return await node_handle_failure(state, session)

    # Add Nodes
    workflow.add_node("parse_intent", _parse_intent)
    workflow.add_node("discover_candidates", _discover_candidates)
    workflow.add_node("verify_and_gatekeep", _verify_and_gatekeep)
    workflow.add_node("create_proposal", _create_proposal)
    workflow.add_node("handle_failure", _handle_failure)

    # Add Edges
    workflow.add_edge(START, "parse_intent")
    workflow.add_edge("parse_intent", "discover_candidates")
    workflow.add_conditional_edges(
        "discover_candidates",
        route_after_discovery,
        {
            "verify_and_gatekeep": "verify_and_gatekeep",
            "handle_failure": "handle_failure",
        },
    )
    workflow.add_conditional_edges(
        "verify_and_gatekeep",
        route_after_gatekeeper,
        {
            "create_proposal": "create_proposal",
            "handle_failure": "handle_failure",
        },
    )
    workflow.add_edge("create_proposal", END)
    workflow.add_edge("handle_failure", END)

    return workflow.compile()
