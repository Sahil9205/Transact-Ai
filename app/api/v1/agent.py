from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import OrderProposal
from app.api.v1.products import get_vector_service_dep
from app.db.database import get_db
from app.domain.schemas import BuyerIntentSchema
from app.services.agent_service import AgentService
from app.services.vector_service import VectorService

router = APIRouter(prefix="/agent", tags=["Autonomous Commerce Agent"])


class AgentChatRequest(BaseModel):
    """Payload for submitting a natural language prompt to the autonomous commerce agent."""
    user_id: str = Field(..., examples=["buyer-demo-1"], description="User ID driving the transaction")
    prompt: str = Field(
        ...,
        examples=["1kg rasgulla chahiye under ₹500 in 110001", "Bhai snacks and sweet lassi for 3 people under 400"],
        description="Buyer request in English, Hindi, or Hinglish",
    )


class AgentChatResponse(BaseModel):
    """Structured response from LangGraph commerce agent workflow execution."""
    user_id: str
    status: str
    agent_message: str
    parsed_intent: BuyerIntentSchema | None
    order_proposal: OrderProposal | None
    step_history: list[str]
    error_details: list[str]


class AgentConfirmRequest(BaseModel):
    """Payload for confirming or rejecting a proposed purchase order."""
    user_id: str = Field(..., description="User ID confirming the order")
    product_id: str = Field(..., description="Product ID from the proposal")
    total_amount_paise: int = Field(..., gt=0, description="Total amount in paise")
    confirmed: bool = Field(default=True, description="True to approve proposal, False to reject")


class AgentConfirmResponse(BaseModel):
    """Confirmation outcome and payment readiness status."""
    user_id: str
    product_id: str
    confirmed: bool
    status: str
    message: str


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Autonomous Commerce Agent",
    description="Submits natural language commerce prompt to the LangGraph state machine. Parses intent, discovers multi-provider products via Qdrant, verifies live price/stock, checks user spending limits, and constructs a verified order proposal.",
)
async def agent_chat_endpoint(
    payload: AgentChatRequest,
    session: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service_dep),
) -> AgentChatResponse:
    """Execute LangGraph autonomous commerce agent workflow."""
    final_state = await AgentService.run_agent(
        session=session,
        user_id=payload.user_id,
        prompt=payload.prompt,
        vector_service=vector_service,
    )

    return AgentChatResponse(
        user_id=final_state["user_id"],
        status=final_state["status"],
        agent_message=final_state["agent_message"],
        parsed_intent=final_state.get("parsed_intent"),
        order_proposal=final_state.get("order_proposal"),
        step_history=final_state.get("step_history", []),
        error_details=final_state.get("error_details", []),
    )


@router.post(
    "/confirm",
    response_model=AgentConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm or Reject Proposed Order",
    description="Records human user confirmation decision in the audit ledger and transitions state to payment readiness.",
)
async def agent_confirm_endpoint(
    payload: AgentConfirmRequest,
    session: AsyncSession = Depends(get_db),
) -> AgentConfirmResponse:
    """Record user confirmation decision on the proposed purchase."""
    res = await AgentService.confirm_proposal(
        session=session,
        user_id=payload.user_id,
        product_id=payload.product_id,
        total_amount_paise=payload.total_amount_paise,
        confirmed=payload.confirmed,
    )

    return AgentConfirmResponse(**res)
