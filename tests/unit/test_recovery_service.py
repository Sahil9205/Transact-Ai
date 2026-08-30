from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, ProductCategory, ProviderType
from app.domain.schemas import BuyerIntentSchema, ProductCreateSchema, ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService
from app.services.recovery_service import RecoveryService


@pytest.mark.asyncio
async def test_failure_diagnosis_classifications() -> None:
    """Test failure diagnosis rules and remediation strategies."""
    # 1. Out of stock
    d1 = RecoveryService.diagnose_failure(
        status="no_candidates",
        error_details=["Product inventory depleted (0 units remaining)"],
        product_name="Rasgulla Box",
    )
    assert d1.failure_code == "OUT_OF_STOCK"
    assert "stock" in d1.human_explanation.lower()

    # 2. Price surge / budget violation
    d2 = RecoveryService.diagnose_failure(
        status="no_candidates",
        error_details=["Price ₹450 exceeds budget ₹300"],
        product_name="Kaju Katli",
    )
    assert d2.failure_code == "PRICE_SURGE"
    assert "budget" in d2.human_explanation.lower()

    # 3. Policy blocked
    d3 = RecoveryService.diagnose_failure(
        status="blocked",
        error_details=["Daily cumulative spending limit exceeded"],
    )
    assert d3.failure_code == "POLICY_BLOCKED"

    # 4. SLA breach
    d4 = RecoveryService.diagnose_failure(
        status="failed",
        error_details=["Merchant prep time 45 mins exceeds 15 min deadline"],
    )
    assert d4.failure_code == "SLA_BREACH"


@pytest.mark.asyncio
async def test_multi_dimensional_alternative_discovery(db_session: AsyncSession) -> None:
    """Test 4-dimensional constraint relaxation in alternative discovery."""
    # 1. Onboard 2 merchants (Local shop + Zepto)
    local_merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    zepto_merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Zepto CP Hub", type=ProviderType.ENTERPRISE, pincode="110001"),
    )

    # 2. Add products:
    # - Local: Gulab Jamun (₹280)
    # - Zepto: Bikano Rasgulla (₹350)
    await ProductService.add_product(
        session=db_session,
        merchant_id=local_merchant.provider_id,
        data=ProductCreateSchema(
            name="Traditional Gulab Jamun",
            category=ProductCategory.SWEETS,
            price_amount=28000,  # ₹280
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
            pincode="110001",
        ),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=zepto_merchant.provider_id,
        data=ProductCreateSchema(
            name="Bikano Rasgulla Tin",
            category=ProductCategory.SWEETS,
            price_amount=35000,  # ₹350
            quantity=15,
            availability_status=AvailabilityStatus.IN_STOCK,
            pincode="110001",
        ),
    )

    # 3. Intent: "Rasgulla under ₹300 in 110001" (No exact match under ₹300 for Rasgulla!)
    intent = BuyerIntentSchema(
        product_query="Rasgulla",
        category=ProductCategory.SWEETS,
        max_price=30000,  # ₹300
        pincode="110001",
    )

    alternatives = await RecoveryService.find_smart_alternatives(
        session=db_session,
        intent=intent,
        limit=3,
    )

    assert len(alternatives) >= 1
    # Check that Zepto Rasgulla was proposed under Price Headroom relaxation (+₹50)
    price_headroom_alts = [a for a in alternatives if a.relaxation_type == "price_headroom"]
    category_alts = [a for a in alternatives if a.relaxation_type == "category_substitute"]

    assert len(price_headroom_alts) >= 1 or len(category_alts) >= 1
    if price_headroom_alts:
        assert price_headroom_alts[0].price_inr == 350.0
        assert price_headroom_alts[0].merchant_name == "Zepto CP Hub"
