from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models import MerchantModel, MerchantStockPingModel, ProductModel
from app.db.repository import (
    AuditRepository,
    MerchantRepository,
    MerchantStockPingRepository,
    ProductRepository,
)
from app.domain.enums import AuditEventType
from app.domain.schemas import StockPingResponse

logger = get_logger(__name__)


class StockPingService:
    """Service managing 6-hour stock staleness detection, real-time merchant alerts, and confirmation heartbeats."""

    @staticmethod
    async def create_or_get_pending_ping(
        session: AsyncSession,
        merchant_id: str,
        product_id: str,
        user_id: str | None = None,
        requested_quantity: int = 1,
        notes: str | None = None,
    ) -> MerchantStockPingModel:
        """Retrieves existing pending verification ping for this product or creates a new one."""
        existing = await MerchantStockPingRepository.get_active_pending_ping(
            session=session,
            merchant_id=merchant_id,
            product_id=product_id,
        )
        if existing:
            logger.info(
                f"Existing pending stock ping found: {existing.ping_id} for merchant {merchant_id} product {product_id}"
            )
            return existing

        ping = await MerchantStockPingRepository.create(
            session=session,
            merchant_id=merchant_id,
            product_id=product_id,
            user_id=user_id,
            requested_quantity=requested_quantity,
            notes=notes or "Stock verification requested due to 6-hour staleness guardrail",
        )

        # Log audit event for observability
        await AuditRepository.log_event(
            session=session,
            event_type=AuditEventType.VERIFICATION_STARTED,
            provider_id=merchant_id,
            product_id=product_id,
            user_id=user_id,
            reason=f"StockVerificationPing {ping.ping_id} dispatched to merchant",
            result="PAUSED_STALE_STOCK",
        )

        return ping

    @staticmethod
    async def list_merchant_pings(
        session: AsyncSession,
        merchant_id: str,
        status: str | None = None,
    ) -> list[StockPingResponse]:
        """Lists stock verification pings for a merchant, enriching each with the product name."""
        pings = await MerchantStockPingRepository.list_by_merchant(
            session=session,
            merchant_id=merchant_id,
            status=status,
        )

        responses: list[StockPingResponse] = []
        for p in pings:
            prod_name = p.product.name if p.product else "Unknown Item"
            responses.append(
                StockPingResponse(
                    ping_id=p.ping_id,
                    merchant_id=p.merchant_id,
                    product_id=p.product_id,
                    product_name=prod_name,
                    user_id=p.user_id,
                    status=p.status,
                    requested_quantity=p.requested_quantity,
                    notes=p.notes,
                    created_at=p.created_at,
                    resolved_at=p.resolved_at,
                )
            )
        return responses

    @staticmethod
    async def confirm_ping(
        session: AsyncSession,
        merchant_id: str,
        ping_id: str,
        available: bool = True,
        new_quantity: int | None = None,
        notes: str | None = None,
    ) -> StockPingResponse:
        """Vendor confirms product is fresh & in-stock, updating product timestamp and unpausing checkouts."""
        ping = await MerchantStockPingRepository.get_by_ping_id(session, ping_id)

        if ping.merchant_id != merchant_id:
            raise ValidationError("Stock ping does not belong to this merchant")

        now = datetime.now(timezone.utc)
        ping.status = "confirmed" if available else "rejected"
        ping.resolved_at = now
        if notes:
            ping.notes = notes

        # Update product stock timestamp and quantity
        product = await ProductRepository.get_by_product_id(session, ping.product_id)
        product.last_stock_updated_at = now
        product.last_verified = now

        if not available:
            product.availability_status = "out_of_stock"
            product.quantity = 0
        else:
            product.availability_status = "in_stock"
            if new_quantity is not None:
                product.quantity = new_quantity
            elif product.quantity == 0:
                product.quantity = max(10, ping.requested_quantity * 5)  # Auto-replenish baseline

        await session.flush()
        await session.refresh(ping)
        await session.refresh(product)

        logger.info(
            f"Merchant {merchant_id} confirmed stock ping {ping_id} (status={ping.status}, product={product.name})"
        )

        return StockPingResponse(
            ping_id=ping.ping_id,
            merchant_id=ping.merchant_id,
            product_id=ping.product_id,
            product_name=product.name,
            user_id=ping.user_id,
            status=ping.status,
            requested_quantity=ping.requested_quantity,
            notes=ping.notes,
            created_at=ping.created_at,
            resolved_at=ping.resolved_at,
        )

    @staticmethod
    async def store_pulse(
        session: AsyncSession,
        merchant_id: str,
    ) -> int:
        """1-tap heartbeat: Re-verifies all active catalog items as fresh for 6 more hours."""
        # Verify merchant exists
        await MerchantRepository.get_by_merchant_id(session, merchant_id)

        now = datetime.now(timezone.utc)

        # 1. Update all products for this merchant
        stmt_prods = select(ProductModel).where(ProductModel.merchant_id == merchant_id)
        res_prods = await session.execute(stmt_prods)
        products = res_prods.scalars().all()

        for p in products:
            p.last_stock_updated_at = now
            p.last_verified = now

        # 2. Mark all pending pings as confirmed
        stmt_pings = select(MerchantStockPingModel).where(
            MerchantStockPingModel.merchant_id == merchant_id,
            MerchantStockPingModel.status == "pending",
        )
        res_pings = await session.execute(stmt_pings)
        pings = res_pings.scalars().all()
        for ping in pings:
            ping.status = "confirmed"
            ping.resolved_at = now
            ping.notes = "Auto-resolved via 1-tap Store Pulse heartbeat"

        await session.flush()
        logger.info(f"Store pulse executed for merchant {merchant_id}: {len(products)} products refreshed")
        return len(products)
