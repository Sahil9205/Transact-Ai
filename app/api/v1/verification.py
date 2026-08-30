from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.gatekeeper_service import GatekeeperDecision, GatekeeperService

router = APIRouter(prefix="/verification", tags=["Verification & Gatekeeper"])


class PreflightVerificationRequest(BaseModel):
    """Payload for initiating pre-flight verification and policy check."""
    user_id: str = Field(..., description="User ID requesting the transaction")
    product_id: str = Field(..., description="Product UUID to verify")
    quantity: int = Field(default=1, ge=1, description="Quantity of items to purchase")
    user_max_price_inr: float | None = Field(
        default=None,
        description="Optional price ceiling in INR specified by the user",
    )
    deadline_time: str | None = Field(
        default=None,
        description="Optional fulfillment deadline string (e.g. '18:30')",
    )


@router.post(
    "/preflight",
    response_model=GatekeeperDecision,
    status_code=status.HTTP_200_OK,
    summary="Pre-Flight Verification & Authorization Check",
    description="Atomically executes authoritative product verification (live price, stock, freshness) and user policy compliance (transaction limit, daily limit, category whitelist) before any payment or order is created.",
)
async def preflight_verification_endpoint(
    payload: PreflightVerificationRequest,
    session: AsyncSession = Depends(get_db),
) -> GatekeeperDecision:
    """Execute atomic pre-flight gatekeeper verification."""
    max_price_paise = int(payload.user_max_price_inr * 100) if payload.user_max_price_inr is not None else None

    return await GatekeeperService.verify_and_authorize(
        session=session,
        user_id=payload.user_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        user_max_price_paise=max_price_paise,
        deadline_time=payload.deadline_time,
    )
