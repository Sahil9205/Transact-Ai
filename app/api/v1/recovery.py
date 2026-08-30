from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.enums import ProductCategory
from app.domain.schemas import BuyerIntentSchema
from app.services.recovery_service import AlternativeOptionSchema, FailureDiagnosis, RecoveryService

router = APIRouter(prefix="/recovery", tags=["Failure Diagnosis & Smart Recovery"])


class DiagnoseFailureRequest(BaseModel):
    """Payload to diagnose a commerce failure."""
    status: str = Field(..., examples=["no_candidates", "blocked"], description="Failure status code")
    error_details: list[str] | None = Field(default=None, description="Detailed failure errors/reasons")
    product_name: str | None = Field(default=None, description="Optional product name that was attempted")


class FindAlternativesRequest(BaseModel):
    """Payload to find smart alternatives via multi-dimensional constraint relaxation."""
    product_query: str = Field(..., examples=["Rasgulla"], description="Target product search query")
    max_price_inr: float | None = Field(default=None, examples=[300.0], description="Optional budget ceiling")
    category: ProductCategory | None = Field(default=None, description="Product category")
    pincode: str | None = Field(default=None, examples=["110001"], description="Serviceable delivery pincode")
    failed_product_id: str | None = Field(default=None, description="Product ID that failed or went out of stock")
    limit: int = Field(default=3, ge=1, le=10, description="Max alternative suggestions to return")


@router.post(
    "/diagnose",
    response_model=FailureDiagnosis,
    status_code=status.HTTP_200_OK,
    summary="Diagnose Commerce Failure",
    description="Classifies why a transaction or search failed (OUT_OF_STOCK, PRICE_SURGE, POLICY_BLOCKED, SLA_BREACH, NO_MATCH) and provides recommended remediation strategy.",
)
async def diagnose_failure_endpoint(
    payload: DiagnoseFailureRequest,
) -> FailureDiagnosis:
    """Diagnose commerce failure cause."""
    return RecoveryService.diagnose_failure(
        status=payload.status,
        error_details=payload.error_details,
        product_name=payload.product_name,
    )


@router.post(
    "/alternatives",
    response_model=list[AlternativeOptionSchema],
    status_code=status.HTTP_200_OK,
    summary="Find Multi-Dimensional Smart Alternatives",
    description="Systematically relaxes constraints across 4 dimensions (Price Headroom, Timeline Extension, Cross-Platform Switching, and Category Substitutes) to find verified in-stock alternatives.",
)
async def find_alternatives_endpoint(
    payload: FindAlternativesRequest,
    session: AsyncSession = Depends(get_db),
) -> list[AlternativeOptionSchema]:
    """Find smart alternatives with 4-dimensional constraint relaxation."""
    max_price_paise = int(payload.max_price_inr * 100) if payload.max_price_inr is not None else None
    intent = BuyerIntentSchema(
        product_query=payload.product_query,
        category=payload.category,
        max_price=max_price_paise,
        pincode=payload.pincode,
    )

    return await RecoveryService.find_smart_alternatives(
        session=session,
        intent=intent,
        failed_product_id=payload.failed_product_id,
        limit=payload.limit,
    )
