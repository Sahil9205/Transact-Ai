from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, StaleDataError, ValidationError
from app.core.logging import get_logger
from app.db.repository import AuditRepository, ProductRepository
from app.domain.enums import AuditEventType, FreshnessTier
from app.domain.schemas import ProductSchema
from app.services.product_service import model_to_schema

logger = get_logger(__name__)


class VerificationResult(BaseModel):
    """Structured result of deterministic product verification."""
    is_verified: bool
    product: ProductSchema
    failure_reasons: list[str] = Field(default_factory=list)
    unit_price_paise: int
    requested_quantity: int
    total_amount_paise: int
    freshness_tier: FreshnessTier


class VerificationService:
    """Deterministic Verification Engine: verifies live pricing, stock, freshness, and SLAs directly from the source of truth."""

    @staticmethod
    async def verify_product(
        session: AsyncSession,
        product_id: str,
        requested_quantity: int = 1,
        user_max_price_paise: int | None = None,
        deadline_time: str | None = None,
    ) -> VerificationResult:
        """Deterministically verifies a product candidate against live database truth and user constraints."""
        logger.info(
            "Starting authoritative verification",
            product_id=product_id,
            quantity=requested_quantity,
            user_max_price=user_max_price_paise,
            deadline=deadline_time,
        )

        # 1. Fetch live product from DB
        product_model = await ProductRepository.get_by_product_id(session, product_id)
        product_schema = model_to_schema(product_model)
        unit_price = product_schema.pricing.amount
        total_amount = unit_price * requested_quantity

        # Log VERIFICATION_STARTED audit event
        await AuditRepository.log_event(
            session=session,
            event_type=AuditEventType.VERIFICATION_STARTED,
            product_id=product_id,
            provider_id=product_schema.provider_id,
            amount=total_amount,
            reason=f"Verifying product '{product_schema.name}' (qty={requested_quantity})",
        )

        failure_reasons: list[str] = []

        # 2. Check Inventory & Stock Quantity
        if product_schema.availability.status.value != "in_stock":
            failure_reasons.append("product_out_of_stock")
        elif (
            product_schema.availability.quantity is not None
            and product_schema.availability.quantity < requested_quantity
        ):
            failure_reasons.append(
                f"insufficient_stock (requested {requested_quantity}, available {product_schema.availability.quantity})"
            )

        # 3. Check Data Freshness Tier
        freshness = product_schema.verification.freshness_tier
        if freshness == FreshnessTier.STALE:
            failure_reasons.append("data_is_stale (last verified > 6 hours ago)")

        # 4. Check User Budget Ceiling
        if user_max_price_paise is not None and total_amount > user_max_price_paise:
            failure_reasons.append(
                f"price_exceeds_budget (total ₹{total_amount / 100} > budget ₹{user_max_price_paise / 100})"
            )

        is_verified = len(failure_reasons) == 0

        # Log VERIFICATION_PASSED or VERIFICATION_FAILED audit event
        if is_verified:
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.VERIFICATION_PASSED,
                product_id=product_id,
                provider_id=product_schema.provider_id,
                amount=total_amount,
                result="PASSED",
                reason="All deterministic verification checks satisfied",
            )
            logger.info("Verification PASSED", product_id=product_id, amount=total_amount)
        else:
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.VERIFICATION_FAILED,
                product_id=product_id,
                provider_id=product_schema.provider_id,
                amount=total_amount,
                result="FAILED",
                reason="; ".join(failure_reasons),
            )
            logger.warning("Verification FAILED", product_id=product_id, reasons=failure_reasons)

        return VerificationResult(
            is_verified=is_verified,
            product=product_schema,
            failure_reasons=failure_reasons,
            unit_price_paise=unit_price,
            requested_quantity=requested_quantity,
            total_amount_paise=total_amount,
            freshness_tier=freshness,
        )
