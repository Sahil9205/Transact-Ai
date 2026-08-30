from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas import ProductSchema
from app.services.policy_service import PolicyEvaluationResult, PolicyService
from app.services.verification_service import VerificationResult, VerificationService

logger = get_logger(__name__)


class GatekeeperDecision(BaseModel):
    """Authoritative decision from the combined pre-flight verification & policy gatekeeper."""
    is_authorized: bool
    decision: str = Field(description="'ALLOW' or 'BLOCK'")
    verified_product: ProductSchema | None = None
    unit_price_inr: float
    total_amount_inr: float
    total_amount_paise: int
    verification_passed: bool
    policy_passed: bool
    blocked_reasons: list[str] = Field(default_factory=list)
    spent_today_inr: float = 0.0
    remaining_daily_budget_inr: float | None = None


class GatekeeperService:
    """Atomic Pre-Flight Gatekeeper combining Authoritative Verification & Spending Policy Enforcement."""

    @staticmethod
    async def verify_and_authorize(
        session: AsyncSession,
        user_id: str,
        product_id: str,
        quantity: int = 1,
        user_max_price_paise: int | None = None,
        deadline_time: str | None = None,
    ) -> GatekeeperDecision:
        """Executes full atomic pre-flight checks: verifies product truth + enforces user spending limits."""
        logger.info(
            "Running pre-flight gatekeeper authorization",
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )

        # Step 1: Authoritative Product Verification
        v_result = await VerificationService.verify_product(
            session=session,
            product_id=product_id,
            requested_quantity=quantity,
            user_max_price_paise=user_max_price_paise,
            deadline_time=deadline_time,
        )

        all_blocked_reasons: list[str] = list(v_result.failure_reasons)
        policy_passed = False
        p_result: PolicyEvaluationResult | None = None

        # Step 2: User Spending Policy Evaluation (only if product exists)
        if v_result.product:
            p_result = await PolicyService.evaluate_policy(
                session=session,
                user_id=user_id,
                category=v_result.product.category,
                amount_paise=v_result.total_amount_paise,
            )
            policy_passed = p_result.is_allowed
            if not policy_passed:
                all_blocked_reasons.extend(p_result.violation_reasons)

        is_authorized = v_result.is_verified and policy_passed

        spent_today_inr = (p_result.spent_today_paise / 100) if p_result else 0.0
        rem_budget_inr = (
            (p_result.remaining_daily_budget_paise / 100)
            if p_result and p_result.remaining_daily_budget_paise is not None
            else None
        )

        return GatekeeperDecision(
            is_authorized=is_authorized,
            decision="ALLOW" if is_authorized else "BLOCK",
            verified_product=v_result.product,
            unit_price_inr=v_result.unit_price_paise / 100,
            total_amount_inr=v_result.total_amount_paise / 100,
            total_amount_paise=v_result.total_amount_paise,
            verification_passed=v_result.is_verified,
            policy_passed=policy_passed,
            blocked_reasons=all_blocked_reasons,
            spent_today_inr=spent_today_inr,
            remaining_daily_budget_inr=rem_budget_inr,
        )
