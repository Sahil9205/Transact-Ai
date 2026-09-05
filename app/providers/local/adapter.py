from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.providers.base import BaseProviderAdapter
from app.db.models import MerchantModel, ProductModel
from app.domain.schemas import (
    ProviderSchema, ProductSchema, PricingSchema, 
    AvailabilitySchema, VerificationSchema, FulfillmentSchema
)
from app.domain.enums import FreshnessTier, ProviderType, ProductCategory, AvailabilityStatus, FulfillmentType, PricingType
from app.core.logging import get_logger
from app.core.exceptions import NotFoundError

class LocalMerchantAdapter(BaseProviderAdapter):
    """Adapter for interacting with local merchants in the database."""
    
    def __init__(self, merchant_id: str, session: AsyncSession) -> None:
        self.merchant_id = merchant_id
        self.session = session
        self.logger = get_logger(__name__)
    
    def _compute_freshness(self, last_verified: datetime) -> FreshnessTier:
        """Deterministic freshness computation. Code decides, not AI."""
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
            
    def _to_product_schema(self, product: ProductModel) -> ProductSchema:
        """Convert ORM model to canonical schema."""
        return ProductSchema(
            product_id=product.product_id,
            provider_id=product.merchant_id,
            name=product.name,
            description=product.description,
            category=ProductCategory(product.category),
            pricing=PricingSchema(
                amount=product.price_amount,
                currency=product.price_currency,
                pricing_type=PricingType(getattr(product, "pricing_type", "fixed_unit")),
                unit=getattr(product, "unit", "piece"),
                min_quantity=getattr(product, "min_quantity", 1.0),
                increment_step=getattr(product, "increment_step", 1.0),
            ),
            availability=AvailabilitySchema(
                status=AvailabilityStatus(product.availability_status),
                quantity=product.quantity
            ),
            fulfillment=FulfillmentSchema(
                type=FulfillmentType(product.fulfillment_type),
                prep_time_minutes=product.prep_time_minutes,
                slot_capacity=product.slot_capacity
            ),
            location=None,
            pincode=product.pincode,
            verification=VerificationSchema(
                last_verified=product.last_verified,
                freshness_tier=self._compute_freshness(product.last_verified)
            )
        )

    async def get_provider_info(self) -> ProviderSchema:
        """Get canonical provider information."""
        stmt = select(MerchantModel).where(MerchantModel.merchant_id == self.merchant_id)
        result = await self.session.execute(stmt)
        merchant = result.scalar_one_or_none()
        
        if not merchant:
            self.logger.error("Merchant not found", merchant_id=self.merchant_id)
            raise NotFoundError(f"Merchant {self.merchant_id} not found")
            
        return ProviderSchema(
            provider_id=merchant.merchant_id,
            name=merchant.name,
            type=ProviderType(merchant.type),
            description=merchant.description,
            location=merchant.location,
            pincode=merchant.pincode,
            is_active=merchant.is_active
        )

    async def search_products(
        self,
        query: str | None = None,
        category: str | None = None,
        pincode: str | None = None,
    ) -> list[ProductSchema]:
        """Search products with optional filters."""
        stmt = select(ProductModel).where(ProductModel.merchant_id == self.merchant_id)
        
        if query:
            stmt = stmt.where(ProductModel.name.ilike(f"%{query}%"))
        if category:
            stmt = stmt.where(ProductModel.category == category)
        if pincode:
            stmt = stmt.where(ProductModel.pincode == pincode)
            
        result = await self.session.execute(stmt)
        products = result.scalars().all()
        
        return [self._to_product_schema(p) for p in products]

    async def get_product(self, product_id: str) -> ProductSchema | None:
        """Get a single product by ID. Returns None if not found."""
        stmt = select(ProductModel).where(
            ProductModel.product_id == product_id,
            ProductModel.merchant_id == self.merchant_id
        )
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            return None
            
        return self._to_product_schema(product)

    async def check_availability(self, product_id: str) -> AvailabilitySchema:
        """Check real-time availability for a product."""
        product = await self.get_product(product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")
            
        return product.availability

    async def get_current_price(self, product_id: str) -> PricingSchema:
        """Get the authoritative current price. This is the source of truth."""
        product = await self.get_product(product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")
            
        return product.pricing
