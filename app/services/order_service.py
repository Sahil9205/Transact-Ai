from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models import MerchantModel, OrderModel, PaymentModel, ProductModel
from app.db.repository import AuditRepository, OrderRepository
from app.domain.enums import AuditEventType, OrderStatus, PaymentStatus

logger = get_logger(__name__)


class OrderSummaryResponse(BaseModel):
    """Detailed summary of an order with merchant, product, and payment status."""
    order_id: str
    user_id: str
    merchant_id: str
    merchant_name: str
    product_id: str
    product_name: str
    quantity: int
    total_amount_inr: float
    total_amount_paise: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    razorpay_order_id: str | None = None
    payment_status: str | None = None


class OrderService:
    """Production Order Lifecycle and Fulfillment Management Service."""

    @staticmethod
    async def get_order_details(session: AsyncSession, order_id: str) -> OrderSummaryResponse:
        """Fetches full order details including merchant name and payment transaction."""
        order = await OrderRepository.get_by_order_id(session, order_id)

        # Lookup merchant
        stmt_m = select(MerchantModel).where(MerchantModel.merchant_id == order.merchant_id)
        res_m = await session.execute(stmt_m)
        merchant = res_m.scalar_one_or_none()
        merchant_name = merchant.name if merchant else "Unknown Merchant"

        # Lookup product
        stmt_p = select(ProductModel).where(ProductModel.product_id == order.product_id)
        res_p = await session.execute(stmt_p)
        product = res_p.scalar_one_or_none()
        product_name = product.name if product else "Unknown Product"

        # Lookup payment
        stmt_pay = select(PaymentModel).where(PaymentModel.order_id == order_id)
        res_pay = await session.execute(stmt_pay)
        payment = res_pay.scalar_one_or_none()

        return OrderSummaryResponse(
            order_id=order.order_id,
            user_id=order.user_id,
            merchant_id=order.merchant_id,
            merchant_name=merchant_name,
            product_id=order.product_id,
            product_name=product_name,
            quantity=order.quantity,
            total_amount_inr=order.total_amount / 100,
            total_amount_paise=order.total_amount,
            currency=order.currency,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            razorpay_order_id=payment.provider_ref if payment else None,
            payment_status=payment.status if payment else None,
        )

    @staticmethod
    async def list_user_orders(
        session: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[OrderSummaryResponse]:
        """Lists order history for a specific user."""
        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(desc(OrderModel.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        orders = result.scalars().all()

        summaries = []
        for order in orders:
            summaries.append(await OrderService.get_order_details(session, order.order_id))
        return summaries

    @staticmethod
    async def list_merchant_orders(
        session: AsyncSession,
        merchant_id: str,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OrderSummaryResponse]:
        """Lists incoming orders for a merchant with optional status filter."""
        stmt = select(OrderModel).where(OrderModel.merchant_id == merchant_id)
        if status_filter:
            stmt = stmt.where(OrderModel.status == status_filter)

        stmt = stmt.order_by(desc(OrderModel.created_at)).offset(offset).limit(limit)
        result = await session.execute(stmt)
        orders = result.scalars().all()

        summaries = []
        for order in orders:
            summaries.append(await OrderService.get_order_details(session, order.order_id))
        return summaries

    @staticmethod
    async def update_fulfillment_status(
        session: AsyncSession,
        order_id: str,
        merchant_id: str,
        new_status: OrderStatus,
    ) -> OrderSummaryResponse:
        """Updates merchant order fulfillment status (e.g. ready_for_pickup, completed)."""
        order = await OrderRepository.get_by_order_id(session, order_id)

        if order.merchant_id != merchant_id:
            raise AuthorizationError(message="Merchant does not own this order.")

        old_status = order.status
        order.status = new_status.value
        await session.commit()

        # Log NOTIFICATION_SENT audit event
        await AuditRepository.log_event(
            session=session,
            event_type=AuditEventType.NOTIFICATION_SENT,
            user_id=order.user_id,
            provider_id=merchant_id,
            order_id=order.order_id,
            product_id=order.product_id,
            amount=order.total_amount,
            reason=f"Order status progressed: {old_status} -> {new_status.value}",
        )

        return await OrderService.get_order_details(session, order_id)

    @staticmethod
    async def cancel_order(
        session: AsyncSession,
        order_id: str,
        user_id: str,
        reason: str = "User requested cancellation",
    ) -> OrderSummaryResponse:
        """Cancels an active order if not already completed."""
        order = await OrderRepository.get_by_order_id(session, order_id)

        if order.user_id != user_id:
            raise AuthorizationError(message="User does not own this order.")

        if order.status == OrderStatus.COMPLETED.value:
            raise ValidationError(message="Cannot cancel an already completed order.")

        old_status = order.status
        order.status = OrderStatus.CANCELLED.value
        await session.commit()

        # Log audit event
        await AuditRepository.log_event(
            session=session,
            event_type=AuditEventType.NOTIFICATION_SENT,
            user_id=user_id,
            order_id=order.order_id,
            product_id=order.product_id,
            amount=order.total_amount,
            reason=f"Order cancelled by user ({reason}) from state '{old_status}'",
        )

        return await OrderService.get_order_details(session, order_id)
