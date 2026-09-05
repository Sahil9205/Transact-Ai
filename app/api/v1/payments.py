from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import OrderModel, PaymentModel
from app.db.repository import OrderRepository
from app.services.payment_service import (
    PaymentOrderResponse,
    PaymentService,
    PaymentVerificationResult,
    WebhookProcessingResult,
)

router = APIRouter(prefix="/payments", tags=["Razorpay Payments"])


class CreatePaymentOrderRequest(BaseModel):
    """Payload to create a new Razorpay payment order for a confirmed product."""
    user_id: str = Field(..., examples=["buyer-1"], description="User ID driving transaction")
    product_id: str = Field(..., description="UUID of product to purchase")
    quantity: int = Field(default=1, ge=1, description="Quantity of items")
    pincode: str | None = Field(default=None, description="6-digit delivery destination pincode")
    delivery_address: str | None = Field(default=None, description="Delivery address provided by user")
    platform: str | None = Field(default=None, description="Calling client platform (e.g. 'claude', 'chatgpt')")
    notes: dict[str, Any] | None = Field(default=None, description="Optional metadata key-values")


class VerifySignatureRequest(BaseModel):
    """Payload containing Razorpay client checkout completion parameters."""
    razorpay_order_id: str = Field(..., description="Razorpay order identifier")
    razorpay_payment_id: str = Field(..., description="Razorpay payment transaction identifier")
    razorpay_signature: str = Field(..., description="Cryptographic HMAC-SHA256 signature from checkout")


class OrderDetailsResponse(BaseModel):
    """Order status and associated payment transaction breakdown."""
    order_id: str
    user_id: str
    merchant_id: str
    product_id: str
    quantity: int
    total_amount_inr: float
    total_amount_paise: int
    currency: str
    status: str
    pincode: str | None = None
    delivery_address: str | None = None
    platform: str | None = None
    razorpay_order_id: str | None = None
    transaction_id: str | None = None
    payment_status: str | None = None


@router.post(
    "/create-order",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay Payment Order",
    description="Initializes a Razorpay order in test mode from a confirmed agent proposal, records the order in local DB, and generates a payment link / checkout session.",
)
async def create_payment_order_endpoint(
    payload: CreatePaymentOrderRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> PaymentOrderResponse:
    """Create Razorpay order and payment link."""
    from app.core.platform import resolve_originating_platform
    detected_platform = resolve_originating_platform(
        explicit_platform=payload.platform,
        headers=request.headers,
    )
    return await PaymentService.create_payment_order(
        session=session,
        user_id=payload.user_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        pincode=payload.pincode,
        delivery_address=payload.delivery_address,
        platform=detected_platform,
        notes=payload.notes,
    )


@router.post(
    "/verify-signature",
    response_model=PaymentVerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Verify Razorpay Payment Signature",
    description="Validates cryptographic HMAC-SHA256 payment signature from client checkout. On match, settles the transaction and marks order as order_created.",
)
async def verify_signature_endpoint(
    payload: VerifySignatureRequest,
    session: AsyncSession = Depends(get_db),
) -> PaymentVerificationResult:
    """Verify client checkout signature cryptographically."""
    return await PaymentService.verify_payment_signature(
        session=session,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )


@router.post(
    "/webhook",
    response_model=WebhookProcessingResult,
    status_code=status.HTTP_200_OK,
    summary="Razorpay Webhook Handler",
    description="Asynchronously receives and processes Razorpay webhook events (payment.captured, order.paid, payment.failed) with signature authentication and idempotency guarantees.",
)
async def razorpay_webhook_endpoint(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    session: AsyncSession = Depends(get_db),
) -> WebhookProcessingResult:
    """Process incoming Razorpay webhook event."""
    body_bytes = await request.body()
    return await PaymentService.process_webhook_event(
        session=session,
        payload_bytes=body_bytes,
        signature_header=x_razorpay_signature,
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Order Settlement Status",
    description="Fetches live order and payment status by internal order ID.",
)
async def get_order_status_endpoint(
    order_id: str,
    session: AsyncSession = Depends(get_db),
) -> OrderDetailsResponse:
    """Fetch order status and payment information."""
    order = await OrderRepository.get_by_order_id(session, order_id)

    stmt = select(PaymentModel).where(PaymentModel.order_id == order_id)
    res = await session.execute(stmt)
    payment = res.scalar_one_or_none()

    return OrderDetailsResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        merchant_id=order.merchant_id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount_inr=order.total_amount / 100,
        total_amount_paise=order.total_amount,
        currency=order.currency,
        status=order.status,
        razorpay_order_id=payment.provider_ref if payment else None,
        transaction_id=payment.transaction_id if payment and payment.transaction_id else getattr(order, "transaction_id", None),
        payment_status=payment.status if payment else None,
    )
