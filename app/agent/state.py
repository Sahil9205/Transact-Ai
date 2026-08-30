from __future__ import annotations

from typing import Any, TypedDict
from pydantic import BaseModel, Field

from app.domain.schemas import BuyerIntentSchema
from app.services.discovery_service import RankedCandidateSchema
from app.services.gatekeeper_service import GatekeeperDecision


class OrderProposal(BaseModel):
    """Final proposal ready for human confirmation and checkout."""
    product_id: str
    product_name: str
    merchant_name: str
    merchant_type: str
    quantity: int
    unit_price_inr: float
    total_amount_inr: float
    total_amount_paise: int
    fulfillment_sla: str
    savings_vs_budget_inr: float | None = None
    remaining_daily_budget_inr: float | None = None
    recommendation_tag: str
    requires_confirmation: bool = True


class CommerceAgentState(TypedDict):
    """Deterministic state tracked across all LangGraph nodes."""
    user_id: str
    raw_prompt: str
    parsed_intent: BuyerIntentSchema | None
    candidates: list[RankedCandidateSchema]
    selected_candidate: RankedCandidateSchema | None
    gatekeeper_decision: GatekeeperDecision | None
    order_proposal: OrderProposal | None
    status: str  # "intent_parsed" | "discovered" | "verified" | "proposed" | "blocked" | "failed"
    agent_message: str
    error_details: list[str]
    step_history: list[str]
