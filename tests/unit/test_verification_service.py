from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import ProductRepository
from app.domain.enums import AvailabilityStatus, FulfillmentType, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService
from app.services.verification_service import VerificationService


@pytest.mark.asyncio
async def test_verification_success(db_session: AsyncSession) -> None:
    """Test successful verification when price, stock, and freshness are all valid."""
    # 1. Onboard merchant & product
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=45000,  # ₹450
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=15,
            pincode="110001",
        ),
    )

    # 2. Verify product
    res = await VerificationService.verify_product(
        session=db_session,
        product_id=product.product_id,
        requested_quantity=2,
        user_max_price_paise=100000,  # Budget ₹1000 >= ₹900
    )

    assert res.is_verified is True
    assert len(res.failure_reasons) == 0
    assert res.unit_price_paise == 45000
    assert res.total_amount_paise == 90000
    assert res.requested_quantity == 2


@pytest.mark.asyncio
async def test_verification_out_of_stock_failure(db_session: AsyncSession) -> None:
    """Test verification fails when requested quantity exceeds available stock."""
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
            quantity=5,  # Only 5 in stock
            availability_status=AvailabilityStatus.IN_STOCK,
        ),
    )

    # Request 10 units (exceeds 5)
    res = await VerificationService.verify_product(
        session=db_session,
        product_id=product.product_id,
        requested_quantity=10,
    )

    assert res.is_verified is False
    assert any("insufficient_stock" in r for r in res.failure_reasons)


@pytest.mark.asyncio
async def test_verification_stale_data_failure(db_session: AsyncSession) -> None:
    """Test verification fails when product verification timestamp is > 6 hours old."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Stale Sweet Box",
            category=ProductCategory.SWEETS,
            price_amount=50000,
            quantity=10,
        ),
    )

    # Manually age the product last_verified timestamp to 8 hours ago
    prod_model = await ProductRepository.get_by_product_id(db_session, product.product_id)
    prod_model.last_verified = datetime.now(timezone.utc) - timedelta(hours=8)
    await db_session.commit()

    res = await VerificationService.verify_product(
        session=db_session,
        product_id=product.product_id,
        requested_quantity=1,
    )

    assert res.is_verified is False
    assert any("data_is_stale" in r for r in res.failure_reasons)


@pytest.mark.asyncio
async def test_verification_budget_ceiling_failure(db_session: AsyncSession) -> None:
    """Test verification fails when total amount exceeds user budget ceiling."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Kaju Katli",
            category=ProductCategory.SWEETS,
            price_amount=80000,  # ₹800
            quantity=10,
        ),
    )

    # User budget ₹500 (50000 paise) < ₹800
    res = await VerificationService.verify_product(
        session=db_session,
        product_id=product.product_id,
        requested_quantity=1,
        user_max_price_paise=50000,
    )

    assert res.is_verified is False
    assert any("price_exceeds_budget" in r for r in res.failure_reasons)
