from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app.domain.enums import (
    AvailabilityStatus,
    FreshnessTier,
    FulfillmentType,
    ProductCategory,
)
from app.domain.schemas import (
    AvailabilitySchema,
    FulfillmentSchema,
    PricingSchema,
    ProductSchema,
    VerificationSchema,
)
from app.services.vector_service import VectorService


@pytest.mark.asyncio
async def test_vector_service_in_memory() -> None:
    """Test VectorService using in-memory Qdrant instance."""
    service = VectorService(qdrant_url=None, collection_name="test_products")
    await service.ensure_collection()

    product = ProductSchema(
        product_id="prod-12345",
        provider_id="mer-67890",
        name="Kolkata Special Rasgulla",
        description="Juicy cottage cheese sponge balls in sweet syrup",
        category=ProductCategory.SWEETS,
        pricing=PricingSchema(amount=45000, currency="INR"),
        availability=AvailabilitySchema(status=AvailabilityStatus.IN_STOCK, quantity=50),
        fulfillment=FulfillmentSchema(type=FulfillmentType.PICKUP, prep_time_minutes=20),
        pincode="110001",
        verification=VerificationSchema(
            last_verified=datetime.now(timezone.utc),
            freshness_tier=FreshnessTier.FRESH,
        ),
    )

    # Upsert product
    await service.upsert_product(product)

    # Search similar
    results = await service.search_similar(query="sweet cheese dessert", limit=5)
    assert len(results) >= 1
    assert results[0]["name"] == "Kolkata Special Rasgulla"
    assert results[0]["price_amount"] == 45000

    # Search with filter
    filtered_results = await service.search_similar(
        query="rasgulla",
        category="sweets",
        max_price=50000,
        pincode="110001",
    )
    assert len(filtered_results) >= 1

    # Search with exceeding filter should return 0 results
    no_results = await service.search_similar(
        query="rasgulla",
        max_price=20000,  # Below 45000
    )
    assert len(no_results) == 0

    # Delete product
    await service.delete_product(product.product_id)
    after_delete = await service.search_similar(query="rasgulla")
    assert len(after_delete) == 0
