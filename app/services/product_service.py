from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import ProductModel
from app.db.repository import AuditRepository, MerchantRepository, ProductRepository
from app.domain.enums import (
    AuditEventType,
    AvailabilityStatus,
    FreshnessTier,
    FulfillmentType,
    ProductCategory,
)
from app.domain.schemas import (
    AvailabilitySchema,
    FulfillmentSchema,
    PricingSchema,
    ProductCreateSchema,
    ProductSchema,
    ProductUpdateSchema,
    VerificationSchema,
)
from app.services.vector_service import VectorService

logger = get_logger(__name__)


def compute_freshness_tier(last_verified: datetime | None) -> FreshnessTier:
    """Computes freshness tier based on the last_verified timestamp."""
    if not last_verified:
        return FreshnessTier.STALE

    if last_verified.tzinfo is None:
        last_verified = last_verified.replace(tzinfo=timezone.utc)

    age = datetime.now(timezone.utc) - last_verified
    hours = age.total_seconds() / 3600
    if hours < 1:
        return FreshnessTier.FRESH
    elif hours < 6:
        return FreshnessTier.STALE_WARNING
    else:
        return FreshnessTier.STALE


def model_to_schema(product: ProductModel) -> ProductSchema:
    """Helper to convert a flat ProductModel ORM object to canonical ProductSchema."""
    return ProductSchema(
        product_id=product.product_id,
        provider_id=product.merchant_id,
        name=product.name,
        description=product.description,
        category=ProductCategory(product.category),
        pricing=PricingSchema(
            amount=product.price_amount,
            currency=product.price_currency,
        ),
        availability=AvailabilitySchema(
            status=AvailabilityStatus(product.availability_status),
            quantity=product.quantity,
        ),
        fulfillment=FulfillmentSchema(
            type=FulfillmentType(product.fulfillment_type),
            prep_time_minutes=product.prep_time_minutes,
            slot_capacity=product.slot_capacity,
        ),
        location=None,
        pincode=product.pincode,
        verification=VerificationSchema(
            last_verified=product.last_verified,
            freshness_tier=compute_freshness_tier(product.last_verified),
        ),
    )


class ProductService:
    """Service for handling product business logic and syncing with Qdrant."""

    @staticmethod
    async def add_product(
        session: AsyncSession,
        merchant_id: str,
        data: ProductCreateSchema,
        vector_service: VectorService | None = None,
    ) -> ProductSchema:
        """Adds a product, upserts to vector service, and logs an audit event."""
        logger.info(f"Adding product '{data.name}' for merchant {merchant_id}")

        # Verify merchant exists
        await MerchantRepository.get_by_merchant_id(session, merchant_id)

        # Create product
        product_model = await ProductRepository.create(session, merchant_id, data)
        schema = model_to_schema(product_model)

        if vector_service:
            try:
                await vector_service.upsert_product(schema)
            except Exception as e:
                logger.warning(f"Vector upsert failed (continuing): {e}")

        await AuditRepository.log_event(
            session,
            event_type=AuditEventType.CANDIDATE_FOUND,
            provider_id=merchant_id,
            product_id=schema.product_id,
            amount=schema.pricing.amount,
            reason=f"Product '{data.name}' added",
            result="SUCCESS",
        )

        return schema

    @staticmethod
    async def update_product(
        session: AsyncSession,
        product_id: str,
        data: ProductUpdateSchema,
        vector_service: VectorService | None = None,
    ) -> ProductSchema:
        """Updates a product, updates vector service, and logs an audit event."""
        logger.info(f"Updating product {product_id}")

        # Update product
        product_model = await ProductRepository.update(session, product_id, data)
        schema = model_to_schema(product_model)

        if vector_service:
            try:
                await vector_service.upsert_product(schema)
            except Exception as e:
                logger.warning(f"Vector upsert failed (continuing): {e}")

        await AuditRepository.log_event(
            session,
            event_type=AuditEventType.FINAL_REVALIDATION,
            product_id=product_id,
            amount=schema.pricing.amount,
            reason=f"Product '{schema.name}' updated",
            result="SUCCESS",
        )

        return schema

    @staticmethod
    async def get_product(session: AsyncSession, product_id: str) -> ProductSchema:
        """Retrieves a product by its ID."""
        logger.debug(f"Retrieving product: {product_id}")
        product_model = await ProductRepository.get_by_product_id(session, product_id)
        return model_to_schema(product_model)

    @staticmethod
    async def search_products(
        session: AsyncSession,
        query: str | None = None,
        category: str | None = None,
        pincode: str | None = None,
        merchant_id: str | None = None,
    ) -> list[ProductSchema]:
        """Searches products using standard DB search."""
        logger.debug(f"Searching products query={query}, category={category}")
        product_models = await ProductRepository.search(
            session,
            query=query,
            category=category,
            pincode=pincode,
            merchant_id=merchant_id,
        )
        return [model_to_schema(p) for p in product_models]
