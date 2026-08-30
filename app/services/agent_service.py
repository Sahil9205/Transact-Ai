from __future__ import annotations

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import build_commerce_agent_graph
from app.agent.state import CommerceAgentState, OrderProposal
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.repository import AuditRepository
from app.domain.enums import AuditEventType
from app.services.vector_service import VectorService

logger = get_logger(__name__)


class AgentService:
    """Orchestration service for the LangGraph-powered autonomous commerce agent."""

    @staticmethod
    async def run_agent(
        session: AsyncSession,
        user_id: str,
        prompt: str,
        vector_service: VectorService | None = None,
    ) -> CommerceAgentState:
        """Executes the full LangGraph state machine from natural language prompt to validated order proposal."""
        logger.info("Executing Commerce Agent workflow", user_id=user_id, prompt=prompt)

        initial_state: CommerceAgentState = {
            "user_id": user_id,
            "raw_prompt": prompt,
            "parsed_intent": None,
            "candidates": [],
            "selected_candidate": None,
            "gatekeeper_decision": None,
            "order_proposal": None,
            "status": "started",
            "agent_message": "",
            "error_details": [],
            "step_history": ["session_started"],
        }

        # Build and compile graph
        graph = build_commerce_agent_graph(session=session, vector_service=vector_service)

        # Configure LangSmith tracing metadata
        settings = get_settings()
        config = {
            "tags": ["transact-ai", "commerce-orchestration"],
            "metadata": {
                "user_id": user_id,
                "environment": settings.APP_ENV,
                "service": "transact-ai-agent",
            },
        }

        # Execute async LangGraph workflow
        final_state: CommerceAgentState = await graph.ainvoke(initial_state, config=config)

        logger.info(
            "Commerce Agent workflow complete",
            user_id=user_id,
            status=final_state.get("status"),
            steps=len(final_state.get("step_history", [])),
        )

        return final_state

    @staticmethod
    async def confirm_proposal(
        session: AsyncSession,
        user_id: str,
        product_id: str,
        total_amount_paise: int,
        confirmed: bool = True,
    ) -> dict[str, Any]:
        """Handles human user confirmation of the proposed purchase order."""
        logger.info(
            "Processing user confirmation",
            user_id=user_id,
            product_id=product_id,
            confirmed=confirmed,
        )

        # Log USER_CONFIRMATION audit event
        await AuditRepository.log_event(
            session=session,
            event_type=AuditEventType.USER_CONFIRMATION,
            user_id=user_id,
            product_id=product_id,
            amount=total_amount_paise,
            result="CONFIRMED" if confirmed else "REJECTED",
            reason=f"User {'confirmed' if confirmed else 'rejected'} order proposal",
        )

        return {
            "user_id": user_id,
            "product_id": product_id,
            "confirmed": confirmed,
            "status": "payment_ready" if confirmed else "user_cancelled",
            "message": "Order confirmed by user. Ready for Razorpay payment initiation." if confirmed else "Order proposal rejected by user.",
        }
