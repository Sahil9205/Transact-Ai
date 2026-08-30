from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.enums import ProductCategory
from app.domain.schemas import SpendingPolicySchema
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["Spending Policies"])


class ConfigurePolicyRequest(BaseModel):
    """Payload for configuring or updating a user's spending policy."""
    max_per_transaction_inr: float = Field(
        ...,
        gt=0,
        examples=[1000.0],
        description="Maximum allowed amount per single transaction in Indian Rupees",
    )
    daily_limit_inr: float = Field(
        ...,
        gt=0,
        examples=[3000.0],
        description="Maximum cumulative spending allowed per calendar day in Indian Rupees",
    )
    allowed_categories: list[ProductCategory] | None = Field(
        default=None,
        examples=[[ProductCategory.SWEETS, ProductCategory.FOOD]],
        description="Optional list of permitted categories (empty allows all categories)",
    )
    is_active: bool = Field(default=True, description="Enable or disable policy enforcement")


class UserPolicyResponse(BaseModel):
    """Response containing active policy and daily spending tracker."""
    policy: SpendingPolicySchema | None
    spent_today_inr: float
    remaining_daily_budget_inr: float | None


@router.post(
    "/users/{user_id}",
    response_model=SpendingPolicySchema,
    status_code=status.HTTP_200_OK,
    summary="Configure User Spending Policy",
    description="Sets deterministic per-transaction and daily spending limits, plus optional category whitelisting for a user.",
)
async def configure_user_policy(
    user_id: str,
    payload: ConfigurePolicyRequest,
    session: AsyncSession = Depends(get_db),
) -> SpendingPolicySchema:
    """Set or update user spending limits and policy rules."""
    max_paise = int(payload.max_per_transaction_inr * 100)
    daily_paise = int(payload.daily_limit_inr * 100)

    return await PolicyService.configure_policy(
        session=session,
        user_id=user_id,
        max_per_transaction_paise=max_paise,
        daily_limit_paise=daily_paise,
        allowed_categories=payload.allowed_categories,
        is_active=payload.is_active,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserPolicyResponse,
    summary="Get User Spending Policy & Balance",
    description="Retrieves a user's configured spending policy, current amount spent today, and remaining daily budget.",
)
async def get_user_policy_status(
    user_id: str,
    session: AsyncSession = Depends(get_db),
) -> UserPolicyResponse:
    """Fetch user spending policy and today's balance."""
    policy = await PolicyService.get_policy(session, user_id)
    spent_today_paise = await PolicyService.calculate_spent_today(session, user_id)
    spent_today_inr = spent_today_paise / 100

    rem_budget_inr = None
    if policy:
        rem_budget_inr = max(0.0, (policy.daily_limit - spent_today_paise) / 100)

    return UserPolicyResponse(
        policy=policy,
        spent_today_inr=spent_today_inr,
        remaining_daily_budget_inr=rem_budget_inr,
    )
