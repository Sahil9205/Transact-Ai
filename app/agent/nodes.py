from __future__ import annotations

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import CommerceAgentState, OrderProposal
from app.core.logging import get_logger
from app.db.repository import AuditRepository
from app.domain.enums import AuditEventType
from app.services.discovery_service import DiscoveryService
from app.services.gatekeeper_service import GatekeeperService
from app.services.intent_service import IntentService
from app.services.recovery_service import AlternativeOptionSchema, RecoveryService
from app.services.vector_service import VectorService

logger = get_logger(__name__)


async def node_parse_intent(
    state: CommerceAgentState,
    session: AsyncSession,
) -> dict[str, Any]:
    """Node 1: Parses raw prompt into structured BuyerIntentSchema."""
    prompt = state.get("raw_prompt", "")
    logger.info("LangGraph Node: parse_intent", prompt=prompt)

    intent = IntentService.parse_intent(prompt)

    # Log INTENT_RECEIVED audit event
    await AuditRepository.log_event(
        session=session,
        event_type=AuditEventType.INTENT_RECEIVED,
        user_id=state.get("user_id"),
        amount=intent.max_price,
        reason=f"Parsed buyer prompt: '{prompt}'",
        metadata={
            "query": intent.product_query,
            "max_price": intent.max_price,
            "deadline": intent.deadline,
            "category": intent.category.value if intent.category else None,
            "pincode": intent.pincode,
        },
    )

    steps = list(state.get("step_history", []))
    steps.append(f"parse_intent: query='{intent.product_query}', budget={intent.max_price}")

    return {
        "parsed_intent": intent,
        "status": "intent_parsed",
        "step_history": steps,
    }


async def node_discover_candidates(
    state: CommerceAgentState,
    session: AsyncSession,
    vector_service: VectorService | None = None,
) -> dict[str, Any]:
    """Node 2: Executes multi-provider hybrid search across all merchants."""
    intent = state.get("parsed_intent")
    if not intent:
        intent = IntentService.parse_intent(state.get("raw_prompt", ""))

    logger.info("LangGraph Node: discover_candidates", query=intent.product_query)

    # Log DISCOVERY_STARTED audit event
    await AuditRepository.log_event(
        session=session,
        event_type=AuditEventType.DISCOVERY_STARTED,
        user_id=state.get("user_id"),
        reason=f"Searching multi-provider catalog for '{intent.product_query}'",
    )

    candidates = await DiscoveryService.match_candidates(
        session=session,
        intent=intent,
        vector_service=vector_service,
    )

    selected = candidates[0] if candidates else None
    steps = list(state.get("step_history", []))
    steps.append(f"discover_candidates: found {len(candidates)} valid candidate(s)")

    return {
        "candidates": candidates,
        "selected_candidate": selected,
        "status": "discovered" if candidates else "no_candidates",
        "step_history": steps,
    }


async def node_verify_and_gatekeep(
    state: CommerceAgentState,
    session: AsyncSession,
) -> dict[str, Any]:
    """Node 3: Authoritatively verifies live pricing/stock and enforces user spending policies."""
    candidate = state.get("selected_candidate")
    user_id = state.get("user_id", "default_user")
    intent = state.get("parsed_intent")

    if not candidate:
        return {
            "status": "no_candidates",
            "error_details": ["No matching candidate to verify."],
        }

    logger.info(
        "LangGraph Node: verify_and_gatekeep",
        product_id=candidate.product.product_id,
        user_id=user_id,
    )

    decision = await GatekeeperService.verify_and_authorize(
        session=session,
        user_id=user_id,
        product_id=candidate.product.product_id,
        quantity=1,
        user_max_price_paise=intent.max_price if intent else None,
        deadline_time=intent.deadline if intent else None,
    )

    steps = list(state.get("step_history", []))
    steps.append(f"verify_and_gatekeep: decision={decision.decision}, authorized={decision.is_authorized}")

    return {
        "gatekeeper_decision": decision,
        "status": "verified" if decision.is_authorized else "blocked",
        "step_history": steps,
        "error_details": decision.blocked_reasons if not decision.is_authorized else [],
    }


async def node_create_proposal(
    state: CommerceAgentState,
    session: AsyncSession,
) -> dict[str, Any]:
    """Node 4: Constructs a clear, finalized order proposal for human approval."""
    candidate = state.get("selected_candidate")
    decision = state.get("gatekeeper_decision")
    user_id = state.get("user_id", "default_user")

    if not candidate or not decision:
        return {"status": "failed", "error_details": ["Incomplete state for proposal creation."]}

    logger.info("LangGraph Node: create_proposal", product=candidate.product.name)

    proposal = OrderProposal(
        product_id=candidate.product.product_id,
        product_name=candidate.product.name,
        merchant_name=candidate.merchant_name,
        merchant_type=candidate.merchant_type,
        quantity=1,
        unit_price_inr=decision.unit_price_inr,
        total_amount_inr=decision.total_amount_inr,
        total_amount_paise=decision.total_amount_paise,
        fulfillment_sla=candidate.fulfillment_sla,
        savings_vs_budget_inr=candidate.savings_vs_budget_inr,
        remaining_daily_budget_inr=decision.remaining_daily_budget_inr,
        recommendation_tag=candidate.recommendation_tag,
        requires_confirmation=True,
    )

    savings_msg = f" (saving ₹{candidate.savings_vs_budget_inr:.2f} vs your budget)" if candidate.savings_vs_budget_inr else ""
    msg = (
        f"🎉 Found the best option! 1x **{proposal.product_name}** from **{proposal.merchant_name}** "
        f"for **₹{proposal.total_amount_inr:.2f}**{savings_msg}.\n"
        f"⏱️ **SLA**: {proposal.fulfillment_sla}\n"
        f"🏷️ **Tag**: {proposal.recommendation_tag}\n\n"
        f"Shall I place this order and generate the secure Razorpay payment link?"
    )

    # Log RECOMMENDATION_CREATED audit event
    await AuditRepository.log_event(
        session=session,
        event_type=AuditEventType.RECOMMENDATION_CREATED,
        user_id=user_id,
        product_id=proposal.product_id,
        amount=proposal.total_amount_paise,
        reason="Agent generated verified order proposal ready for user confirmation",
        metadata={
            "merchant_name": proposal.merchant_name,
            "total_inr": proposal.total_amount_inr,
            "sla": proposal.fulfillment_sla,
        },
    )

    steps = list(state.get("step_history", []))
    steps.append("create_proposal: order proposal constructed and ready for user approval")

    return {
        "order_proposal": proposal,
        "agent_message": msg,
        "status": "proposed",
        "step_history": steps,
    }


async def node_handle_failure(
    state: CommerceAgentState,
    session: AsyncSession,
) -> dict[str, Any]:
    """Node 5: Formulates clear, informative failure messages with multi-dimensional smart alternatives."""
    status = state.get("status", "failed")
    error_details = state.get("error_details", [])
    intent = state.get("parsed_intent")
    if not intent:
        intent = IntentService.parse_intent(state.get("raw_prompt", ""))

    logger.info("LangGraph Node: handle_failure", status=status, errors=error_details)

    # Search for multi-dimensional smart alternatives
    alternatives = await RecoveryService.find_smart_alternatives(
        session=session,
        intent=intent,
        limit=3,
    )

    if status == "no_candidates":
        base_msg = "😔 Aapke exact search criteria (budget / location) par direct match nahi mila."
    elif status == "blocked":
        reasons_formatted = "\n- ".join(error_details) if error_details else "Policy or verification failure"
        base_msg = (
            f"🚫 Direct order proceed nahi ho sakta due to security & spending checks:\n"
            f"- {reasons_formatted}"
        )
    else:
        base_msg = f"⚠️ Issue occurred: {'; '.join(error_details)}"

    # If alternatives exist, append rich comparison
    if alternatives:
        alt_lines = []
        for i, alt in enumerate(alternatives, start=1):
            alt_lines.append(
                f"{i}. **{alt.product.name}** via **{alt.merchant_name}** — **₹{alt.price_inr:.2f}** ({alt.fulfillment_sla})\n   _{alt.difference_explanation}_"
            )
        alt_text = "\n\n💡 **Maine yeh best alternatives dhoondhe hain:**\n" + "\n".join(alt_lines) + "\n\nKya aap inme se koi choose karna chahenge?"
        full_msg = f"{base_msg}{alt_text}"
    else:
        full_msg = f"{base_msg}\n\nTry broadening your budget or checking back shortly."

    steps = list(state.get("step_history", []))
    steps.append(f"handle_failure: {status} (proposed {len(alternatives)} alternative(s))")

    return {
        "agent_message": full_msg,
        "alternatives": alternatives,
        "status": status,
        "step_history": steps,
    }
