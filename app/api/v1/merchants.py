from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.schemas import ProviderCreateSchema, ProviderSchema
from app.services.merchant_service import MerchantService

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post(
    "/",
    response_model=ProviderSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new merchant",
    description="Registers a new merchant or commerce provider and logs the onboarding audit event.",
)
async def register_merchant(
    data: ProviderCreateSchema,
    session: AsyncSession = Depends(get_db),
) -> ProviderSchema:
    """Register a new merchant provider."""
    return await MerchantService.register_merchant(session, data)


@router.get(
    "/",
    response_model=list[ProviderSchema],
    summary="List all active merchants",
    description="Retrieves a list of all active registered merchants.",
)
async def list_merchants(
    session: AsyncSession = Depends(get_db),
) -> list[ProviderSchema]:
    """List all active merchants."""
    return await MerchantService.list_merchants(session)


@router.post(
    "/seed",
    summary="Seed catalog with demo merchants and products",
    description="Populates the relational database with demo commerce providers (Sharma Sweets, Blinkit, Zepto, Amazon) and essential grocery items.",
)
async def seed_merchants(
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Seed catalog with initial merchants and products."""
    from typing import Any
    from app.db.seed import seed_database
    from app.services.vector_service import get_vector_service
    vs = get_vector_service()
    await seed_database(session, vs)
    merchants = await MerchantService.list_merchants(session)
    return {
        "status": "success",
        "total_merchants": len(merchants),
        "merchants": [m.name for m in merchants],
    }


@router.get(
    "/{merchant_id}",
    response_model=ProviderSchema,
    summary="Get merchant by ID",
    description="Fetches specific merchant details by their unique merchant_id UUID.",
)
async def get_merchant(
    merchant_id: str,
    session: AsyncSession = Depends(get_db),
) -> ProviderSchema:
    """Get details of a specific merchant."""
    return await MerchantService.get_merchant(session, merchant_id)

