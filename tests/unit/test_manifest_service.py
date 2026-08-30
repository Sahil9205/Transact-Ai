from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, FulfillmentType, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService
from app.services.manifest_service import ManifestService


@pytest.mark.asyncio
async def test_generate_merchant_manifest(db_session: AsyncSession) -> None:
    """Test generating a dynamic agent manifest for a specific merchant."""
    # 1. Onboard a merchant
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(
            name="Haldiram Sweets & Snacks",
            type=ProviderType.LOCAL_MERCHANT,
            description="Famous sweets and savory snacks",
            location="Chandni Chowk, Delhi",
            pincode="110006",
        ),
    )

    # 2. Add products across 2 categories
    await ProductService.add_product(
        db_session,
        merchant.provider_id,
        ProductCreateSchema(
            name="Rajbhog",
            description="Giant saffron rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=50000,  # ₹500
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=15,
            pincode="110006",
        ),
    )
    await ProductService.add_product(
        db_session,
        merchant.provider_id,
        ProductCreateSchema(
            name="Kaju Roll",
            description="Cashew rolls with pista filling",
            category=ProductCategory.SWEETS,
            price_amount=90000,  # ₹900
            quantity=15,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=10,
            pincode="110006",
        ),
    )
    await ProductService.add_product(
        db_session,
        merchant.provider_id,
        ProductCreateSchema(
            name="Paneer Bread Pakora",
            description="Spicy deep fried bread fritters",
            category=ProductCategory.FOOD,
            price_amount=4000,  # ₹40
            quantity=50,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=5,
            pincode="110006",
        ),
    )

    # 3. Generate manifest
    manifest = await ManifestService.generate_merchant_manifest(db_session, merchant.provider_id)
    assert manifest.provider_id == merchant.provider_id
    assert manifest.name == "Haldiram Sweets & Snacks"
    assert manifest.total_active_products == 3
    assert len(manifest.categories) == 2

    # Check categories
    sweets_summary = next(c for c in manifest.categories if c.category == "sweets")
    assert sweets_summary.product_count == 2
    assert sweets_summary.min_price_amount == 50000
    assert sweets_summary.max_price_amount == 90000

    food_summary = next(c for c in manifest.categories if c.category == "food")
    assert food_summary.product_count == 1
    assert food_summary.min_price_amount == 4000
    assert food_summary.max_price_amount == 4000

    # Check available tools for AI agents
    assert len(manifest.available_tools) >= 2
    tool_names = [t.name for t in manifest.available_tools]
    assert "search_merchant_products" in tool_names
    assert "get_product_details" in tool_names


@pytest.mark.asyncio
async def test_generate_global_manifest(db_session: AsyncSession) -> None:
    """Test generating the global directory manifest."""
    m1 = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Shop 1", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    m2 = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Shop 2", type=ProviderType.ENTERPRISE, pincode="110002"),
    )

    global_manifest = await ManifestService.generate_global_manifest(db_session)
    assert global_manifest.total_merchants >= 2
    provider_ids = [m.provider_id for m in global_manifest.merchants]
    assert m1.provider_id in provider_ids
    assert m2.provider_id in provider_ids
    assert "110001" in global_manifest.supported_pincodes
    assert "110002" in global_manifest.supported_pincodes


@pytest.mark.asyncio
async def test_generate_schema_org_jsonld(db_session: AsyncSession) -> None:
    """Test generating Schema.org JSON-LD metadata for a merchant."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(
            name="Delhi Chaat Corner",
            type=ProviderType.LOCAL_MERCHANT,
            location="Old Delhi",
            pincode="110006",
        ),
    )
    await ProductService.add_product(
        db_session,
        merchant.provider_id,
        ProductCreateSchema(
            name="Aloo Tikki",
            category=ProductCategory.FOOD,
            price_amount=6000,
            quantity=100,
        ),
    )

    jsonld = await ManifestService.generate_schema_org_jsonld(db_session, merchant.provider_id)
    assert jsonld["@context"] == "https://schema.org"
    assert jsonld["@type"] == "Store"
    assert jsonld["name"] == "Delhi Chaat Corner"
    assert "hasOfferCatalog" in jsonld
    offers = jsonld["hasOfferCatalog"]["itemListElement"]
    assert len(offers) == 1
    assert offers[0]["name"] == "Aloo Tikki"
    assert offers[0]["price"] == "60.00"
