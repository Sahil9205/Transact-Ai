from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.enums import OrderStatus
from app.services.audit_service import AuditService, OrderTimelineResponse
from app.services.order_service import OrderService, OrderSummaryResponse

router = APIRouter(prefix="/orders", tags=["Order Management"])


class UpdateFulfillmentStatusRequest(BaseModel):
    """Payload to transition an order's fulfillment state."""
    merchant_id: str = Field(..., description="Merchant ID authorizing status change")
    status: OrderStatus = Field(..., description="Target OrderStatus (e.g. ready_for_pickup, completed)")


class CancelOrderRequest(BaseModel):
    """Payload to cancel an order."""
    user_id: str = Field(..., description="User ID requesting cancellation")
    reason: str = Field(default="User cancellation", description="Reason for cancellation")


@router.get(
    "/{order_id}",
    response_model=OrderSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Order Details",
    description="Fetches full order details including merchant name, product info, and payment settlement status.",
)
async def get_order_endpoint(
    order_id: str,
    session: AsyncSession = Depends(get_db),
) -> OrderSummaryResponse:
    """Retrieve full order details by order ID."""
    return await OrderService.get_order_details(session, order_id)


@router.get(
    "/users/{user_id}",
    response_model=list[OrderSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List User Order History",
    description="Retrieves chronological order history for a specific buyer.",
)
async def list_user_orders_endpoint(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> list[OrderSummaryResponse]:
    """List all orders for a buyer."""
    return await OrderService.list_user_orders(session, user_id, limit=limit, offset=offset)


@router.get(
    "/merchants/{merchant_id}",
    response_model=list[OrderSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Merchant Incoming Orders",
    description="Retrieves incoming orders queue for a specific merchant with optional status filtering.",
)
async def list_merchant_orders_endpoint(
    merchant_id: str,
    status_filter: str | None = Query(default=None, description="Filter by order status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> list[OrderSummaryResponse]:
    """List incoming orders for a merchant."""
    return await OrderService.list_merchant_orders(
        session, merchant_id, status_filter=status_filter, limit=limit, offset=offset
    )


@router.post(
    "/{order_id}/status",
    response_model=OrderSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Fulfillment Status",
    description="Transitions an order along its fulfillment lifecycle (e.g. order_created -> ready_for_pickup -> completed).",
)
async def update_status_endpoint(
    order_id: str,
    payload: UpdateFulfillmentStatusRequest,
    session: AsyncSession = Depends(get_db),
) -> OrderSummaryResponse:
    """Update order fulfillment status."""
    return await OrderService.update_fulfillment_status(
        session=session,
        order_id=order_id,
        merchant_id=payload.merchant_id,
        new_status=payload.status,
    )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Order",
    description="Cancels an active order if not yet completed.",
)
async def cancel_order_endpoint(
    order_id: str,
    payload: CancelOrderRequest,
    session: AsyncSession = Depends(get_db),
) -> OrderSummaryResponse:
    """Cancel an active order."""
    return await OrderService.cancel_order(
        session=session,
        order_id=order_id,
        user_id=payload.user_id,
        reason=payload.reason,
    )


@router.get(
    "/{order_id}/timeline",
    response_model=OrderTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Order Audit Timeline",
    description="Reconstructs the full chronological audit ledger timeline for an order from intent parsing to fulfillment.",
)
async def get_order_timeline_endpoint(
    order_id: str,
    session: AsyncSession = Depends(get_db),
) -> OrderTimelineResponse:
    """Retrieve full chronological audit trail for an order."""
    return await AuditService.get_order_timeline(session, order_id)
