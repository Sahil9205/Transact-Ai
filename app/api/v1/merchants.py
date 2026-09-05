from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.schemas import (
    ProviderCreateSchema,
    ProviderSchema,
    ProviderUpdateSchema,
)
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


@router.patch(
    "/{merchant_id}",
    response_model=ProviderSchema,
    summary="Update merchant profile",
    description="Updates contact information, business category, location, or status for a merchant.",
)
async def update_merchant(
    merchant_id: str,
    data: ProviderUpdateSchema,
    session: AsyncSession = Depends(get_db),
) -> ProviderSchema:
    """Update existing merchant provider details."""
    update_data = data.model_dump(exclude_unset=True)
    return await MerchantService.update_merchant(session, merchant_id, update_data)


@router.post(
    "/{merchant_id}/activate",
    response_model=ProviderSchema,
    summary="Activate merchant provider",
    description="Transitions merchant onboarding_status to active and ensures is_active is true.",
)
async def activate_merchant(
    merchant_id: str,
    session: AsyncSession = Depends(get_db),
) -> ProviderSchema:
    """Activate a merchant provider."""
    return await MerchantService.update_merchant(
        session, merchant_id, {"onboarding_status": "active", "is_active": True}
    )


@router.get(
    "/{merchant_id}/dashboard-stats",
    summary="Merchant Dashboard Real-Time Metrics",
    description="Fetches live aggregated metrics (total products, orders count, revenue in INR, platform breakdown, and recent orders) for the merchant.",
)
async def get_merchant_dashboard_stats(
    merchant_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Retrieve real-time dashboard analytics for a merchant."""
    stats = await MerchantService.get_dashboard_stats(session, merchant_id)
    # Convert ORM Order objects in recent_orders to dicts for clean JSON serialization
    recent_orders = [
        {
            "order_id": o.order_id,
            "product_id": o.product_id,
            "quantity": o.quantity,
            "total_amount_inr": round(o.total_amount / 100, 2),
            "status": o.status,
            "platform": o.platform or "unknown",
            "pincode": o.pincode,
            "delivery_address": o.delivery_address,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in stats["recent_orders"]
    ]
    return {
        "merchant": stats["merchant"].model_dump(mode="json"),
        "total_products": stats["total_products"],
        "total_orders": stats["total_orders"],
        "total_revenue_inr": stats["total_revenue_inr"],
        "platform_breakdown": stats["platform_breakdown"],
        "recent_orders": recent_orders,
        "products": stats.get("products", []),
    }


@router.post(
    "/{merchant_id}/status",
    response_model=ProviderSchema,
    summary="Update store operational status",
    description="Toggles store operational status between open, paused, or closed.",
)
async def update_store_status(
    merchant_id: str,
    status_payload: dict,
    session: AsyncSession = Depends(get_db),
) -> ProviderSchema:
    """Toggle store operational status (open, paused, closed)."""
    new_status = status_payload.get("operational_status", "open")
    return await MerchantService.set_operational_status(session, merchant_id, new_status)


@router.post(
    "/{merchant_id}/products/{product_id}/availability",
    summary="Toggle product availability status",
    description="Sets a product's availability status (in_stock, out_of_stock, limited).",
)
async def toggle_product_availability(
    merchant_id: str,
    product_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_db),
):
    """Update availability status of a product."""
    new_status = payload.get("availability_status", "in_stock")
    return await MerchantService.set_product_availability(session, product_id, new_status)


