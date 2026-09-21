from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.gatekeeper_service import GatekeeperService
from app.services.merchant_service import MerchantService
from app.services.policy_service import PolicyService
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_gatekeeper_authorization_allow(db_session: AsyncSession) -> None:
    """Test gatekeeper successfully authorizes valid product with compliant user policy."""
    # 1. Onboard merchant & product @ ₹450
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT),
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
        ),
    )

    # 2. Configure user policy (max ₹1000 per tx, daily ₹3000)
    user_id = "user-auth-pass"
    await PolicyService.configure_policy(
        session=db_session,
        user_id=user_id,
        max_per_transaction_paise=100000,
        daily_limit_paise=300000,
    )

    # 3. Pre-flight check
    decision = await GatekeeperService.verify_and_authorize(
        session=db_session,
        user_id=user_id,
        product_id=product.product_id,
        quantity=1,
    )

    assert decision.is_authorized is True
    assert decision.decision == "ALLOW"
    assert decision.verification_passed is True
    assert decision.policy_passed is True
    assert decision.unit_price_inr == 450.0
    assert decision.total_amount_inr == 450.0
    assert len(decision.blocked_reasons) == 0


@pytest.mark.asyncio
async def test_gatekeeper_authorization_blocked_by_policy(db_session: AsyncSession) -> None:
    """Test gatekeeper blocks an otherwise valid product if user policy is violated."""
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
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
        ),
    )

    # User policy strictly allows max ₹500 per transaction
    user_id = "user-auth-block"
    await PolicyService.configure_policy(
        session=db_session,
        user_id=user_id,
        max_per_transaction_paise=50000,  # Max ₹500 < ₹800
        daily_limit_paise=100000,
    )

    decision = await GatekeeperService.verify_and_authorize(
        session=db_session,
        user_id=user_id,
        product_id=product.product_id,
        quantity=1,
    )

    assert decision.is_authorized is False
    assert decision.decision == "BLOCK"
    assert decision.verification_passed is True
    assert decision.policy_passed is False
    assert any("per_transaction_limit_exceeded" in r for r in decision.blocked_reasons)


@pytest.mark.asyncio
async def test_gatekeeper_preflight_token_generation_and_validation(db_session: AsyncSession) -> None:
    """Test that preflight token is generated on authorization and verifies properly."""
    user_id = "user-token-1"
    product_id = "prod-token-1"
    qty = 2
    amount_paise = 90000

    token = GatekeeperService.generate_preflight_token(
        user_id=user_id,
        product_id=product_id,
        quantity=qty,
        amount_paise=amount_paise,
    )

    assert isinstance(token, str)
    assert "." in token

    # Valid token verification
    is_valid, err = GatekeeperService.verify_preflight_token(
        token=token,
        user_id=user_id,
        product_id=product_id,
        quantity=qty,
    )
    assert is_valid is True
    assert err is None


@pytest.mark.asyncio
async def test_gatekeeper_preflight_token_tampered_fails(db_session: AsyncSession) -> None:
    """Test that tampered preflight tokens fail verification."""
    token = GatekeeperService.generate_preflight_token(
        user_id="user-tamper",
        product_id="prod-tamper",
        quantity=1,
        amount_paise=50000,
    )

    # 1. Tampered payload
    tampered_token = "bW9ja19mYWtl_payload." + token.split(".")[1]
    is_valid, err = GatekeeperService.verify_preflight_token(
        token=tampered_token,
        user_id="user-tamper",
        product_id="prod-tamper",
        quantity=1,
    )
    assert is_valid is False
    assert "Invalid cryptographic preflight signature" in str(err)

    # 2. Parameter mismatch
    is_valid_user, err_user = GatekeeperService.verify_preflight_token(
        token=token,
        user_id="different-user",
        product_id="prod-tamper",
        quantity=1,
    )
    assert is_valid_user is False
    assert "Token user mismatch" in str(err_user)


@pytest.mark.asyncio
async def test_gatekeeper_preflight_token_expired_fails(db_session: AsyncSession) -> None:
    """Test that an expired preflight token fails verification."""
    # Generate token with negative TTL (already expired)
    token = GatekeeperService.generate_preflight_token(
        user_id="user-exp",
        product_id="prod-exp",
        quantity=1,
        amount_paise=50000,
        ttl_seconds=-10,
    )

    is_valid, err = GatekeeperService.verify_preflight_token(
        token=token,
        user_id="user-exp",
        product_id="prod-exp",
        quantity=1,
    )
    assert is_valid is False
    assert "Preflight token has expired" in str(err)

