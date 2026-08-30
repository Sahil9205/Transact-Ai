from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import (
    AvailabilityStatus,
    FulfillmentType,
    ProductCategory,
    ProviderType,
)
from app.domain.schemas import (
    ProductCreateSchema,
    ProductUpdateSchema,
    ProviderCreateSchema,
)
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService
from app.services.vector_service import VectorService
from app.core.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_add_and_get_product(db_session: AsyncSession) -> None:
    """Test adding a product to a merchant catalog and fetching it."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )

    vector_service = VectorService(collection_name="test_prod_service")
    await vector_service.ensure_collection()

    product_data = ProductCreateSchema(
        name="Rasgulla 1kg",
        description="Fresh Bengali sweet",
        category=ProductCategory.SWEETS,
        price_amount=45000,
        price_currency="INR",
        quantity=25,
        availability_status=AvailabilityStatus.IN_STOCK,
        fulfillment_type=FulfillmentType.PICKUP,
        prep_time_minutes=15,
        pincode="110001",
    )

    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=product_data,
        vector_service=vector_service,
    )

    assert product.name == "Rasgulla 1kg"
    assert product.pricing.amount == 45000
    assert product.provider_id == merchant.provider_id

    # Fetch product
    fetched = await ProductService.get_product(db_session, product.product_id)
    assert fetched.product_id == product.product_id
    assert fetched.name == "Rasgulla 1kg"


@pytest.mark.asyncio
async def test_update_product(db_session: AsyncSession) -> None:
    """Test updating product price and inventory."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT),
    )

    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Gulab Jamun",
            category=ProductCategory.SWEETS,
            price_amount=40000,
            quantity=20,
        ),
    )

    updated = await ProductService.update_product(
        session=db_session,
        product_id=product.product_id,
        data=ProductUpdateSchema(price_amount=42000, quantity=15),
    )

    assert updated.pricing.amount == 42000
    assert updated.availability.quantity == 15


@pytest.mark.asyncio
async def test_search_products(db_session: AsyncSession) -> None:
    """Test searching products by query, category, and pincode."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )

    await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Jalebi",
            category=ProductCategory.SWEETS,
            price_amount=30000,
            pincode="110001",
        ),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Samosa",
            category=ProductCategory.FOOD,
            price_amount=2000,
            pincode="110001",
        ),
    )

    # Search by category
    sweets = await ProductService.search_products(db_session, category="sweets")
    assert any(p.name == "Jalebi" for p in sweets)
    assert not any(p.name == "Samosa" for p in sweets)

    # Search by query
    samosa_results = await ProductService.search_products(db_session, query="samosa")
    assert len(samosa_results) == 1
    assert samosa_results[0].name == "Samosa"


@pytest.mark.asyncio
async def test_add_product_to_nonexistent_merchant_fails(db_session: AsyncSession) -> None:
    """Test adding product to an invalid merchant raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await ProductService.add_product(
            session=db_session,
            merchant_id="invalid-merchant-id",
            data=ProductCreateSchema(
                name="Test",
                category=ProductCategory.GENERAL,
                price_amount=1000,
            ),
        )
