from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, FulfillmentType, ProductCategory, ProviderType
from app.domain.schemas import BuyerIntentSchema, ProductCreateSchema, ProviderCreateSchema
from app.services.discovery_service import DiscoveryService
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService
from app.services.vector_service import VectorService


@pytest.mark.asyncio
async def test_hybrid_discovery_and_ranking(db_session: AsyncSession) -> None:
    """Test multi-provider hybrid candidate matching and deterministic ranking."""
    vector_service = VectorService(collection_name="test_discovery_coll")
    await vector_service.ensure_collection()

    # 1. Onboard Sharma Sweets (Local Merchant @ ₹450 / 20 min pickup)
    sharma = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(
            name="Sharma Sweets",
            type=ProviderType.LOCAL_MERCHANT,
            pincode="110001",
        ),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=sharma.provider_id,
        data=ProductCreateSchema(
            name="Traditional Rasgulla",
            description="Pure chhena spongy rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=45000,  # ₹450
            quantity=50,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=20,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # 2. Onboard Blinkit (Enterprise @ ₹380 / 10 min delivery)
    blinkit = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(
            name="Blinkit Dark Store",
            type=ProviderType.ENTERPRISE,
            pincode="110001",
        ),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=blinkit.provider_id,
        data=ProductCreateSchema(
            name="Haldiram Rasgulla Tin",
            description="Packaged tin rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=38000,  # ₹380
            quantity=30,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.DELIVERY,
            prep_time_minutes=10,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # 3. Onboard Zepto (Enterprise @ ₹350 / 8 min delivery)
    zepto = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(
            name="Zepto CP Hub",
            type=ProviderType.ENTERPRISE,
            pincode="110001",
        ),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=zepto.provider_id,
        data=ProductCreateSchema(
            name="Bikano Rasgulla Tin",
            description="Bikano sweet tin",
            category=ProductCategory.SWEETS,
            price_amount=35000,  # ₹350
            quantity=40,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.DELIVERY,
            prep_time_minutes=8,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # 4. Onboard Premium Sweet Box @ ₹650 (Exceeds ₹500 budget)
    await ProductService.add_product(
        session=db_session,
        merchant_id=sharma.provider_id,
        data=ProductCreateSchema(
            name="Royal Rasgulla Gift Box",
            description="Luxury gift tin",
            category=ProductCategory.SWEETS,
            price_amount=65000,  # ₹650 (Exceeds ₹500 budget)
            quantity=10,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=15,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # 5. Search with budget ₹500 (50000 paise)
    intent = BuyerIntentSchema(
        product_query="rasgulla",
        max_price=50000,
        category=ProductCategory.SWEETS,
        pincode="110001",
    )

    candidates = await DiscoveryService.match_candidates(
        session=db_session,
        intent=intent,
        vector_service=vector_service,
    )

    # Royal Rasgulla (₹650) MUST be excluded by hard filter!
    assert len(candidates) == 3
    names = [c.product.name for c in candidates]
    assert "Royal Rasgulla Gift Box" not in names
    assert "Bikano Rasgulla Tin" in names
    assert "Haldiram Rasgulla Tin" in names
    assert "Traditional Rasgulla" in names

    # Zepto (₹350 / 8 min) should be Rank 1 (Cheapest & Fastest)
    assert candidates[0].product.name == "Bikano Rasgulla Tin"
    assert candidates[0].rank == 1
    assert candidates[0].price_inr == 350.0
    assert candidates[0].savings_vs_budget_inr == 150.0  # ₹500 - ₹350 = ₹150 saved
    assert "Cheapest & Fastest" in candidates[0].recommendation_tag or "Best Price" in candidates[0].recommendation_tag
