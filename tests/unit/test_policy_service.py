from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OrderModel
from app.domain.enums import OrderStatus, PaymentStatus, ProductCategory
from app.services.policy_service import PolicyService


@pytest.mark.asyncio
async def test_policy_configuration_and_retrieval(db_session: AsyncSession) -> None:
    """Test creating and retrieving a user spending policy."""
    policy = await PolicyService.configure_policy(
        session=db_session,
        user_id="user-test-1",
        max_per_transaction_paise=100000,  # ₹1,000
        daily_limit_paise=300000,          # ₹3,000
        allowed_categories=[ProductCategory.SWEETS, ProductCategory.FOOD],
    )

    assert policy.user_id == "user-test-1"
    assert policy.max_per_transaction == 100000
    assert policy.daily_limit == 300000
    assert ProductCategory.SWEETS in policy.allowed_categories
    assert ProductCategory.FOOD in policy.allowed_categories

    fetched = await PolicyService.get_policy(db_session, "user-test-1")
    assert fetched is not None
    assert fetched.max_per_transaction == 100000


@pytest.mark.asyncio
async def test_policy_per_transaction_limit_violation(db_session: AsyncSession) -> None:
    """Test policy blocks orders exceeding the per-transaction ceiling."""
    await PolicyService.configure_policy(
        session=db_session,
        user_id="user-tx-limit",
        max_per_transaction_paise=50000,  # Max ₹500
        daily_limit_paise=200000,         # Daily ₹2000
    )

    # Attempt purchase of ₹800 (80000 paise > 50000 paise)
    res = await PolicyService.evaluate_policy(
        session=db_session,
        user_id="user-tx-limit",
        category=ProductCategory.SWEETS,
        amount_paise=80000,
    )

    assert res.is_allowed is False
    assert res.decision == "BLOCK"
    assert any("per_transaction_limit_exceeded" in r for r in res.violation_reasons)


@pytest.mark.asyncio
async def test_policy_daily_limit_violation(db_session: AsyncSession) -> None:
    """Test policy tracks cumulative daily spend and blocks when daily ceiling is exceeded."""
    user_id = "user-daily-limit"
    await PolicyService.configure_policy(
        session=db_session,
        user_id=user_id,
        max_per_transaction_paise=100000,  # Max ₹1,000 per tx
        daily_limit_paise=120000,          # Daily limit ₹1,200
    )

    # 1. Simulate an existing completed order today of ₹800 (80000 paise)
    await PolicyService.get_or_create_user(db_session, user_id)
    order = OrderModel(
        order_id="order-past-1",
        user_id=user_id,
        merchant_id="mer-1",
        product_id="prod-1",
        quantity=1,
        total_amount=80000,  # ₹800 already spent
        status=OrderStatus.COMPLETED.value,
    )
    db_session.add(order)
    await db_session.commit()

    # 2. Attempt a new purchase of ₹500 (50000 paise).
    # ₹800 spent + ₹500 new = ₹1300 > ₹1200 daily limit!
    res = await PolicyService.evaluate_policy(
        session=db_session,
        user_id=user_id,
        category=ProductCategory.SWEETS,
        amount_paise=50000,
    )

    assert res.is_allowed is False
    assert res.decision == "BLOCK"
    assert any("daily_spending_limit_exceeded" in r for r in res.violation_reasons)
    assert res.spent_today_paise == 80000


@pytest.mark.asyncio
async def test_policy_category_restriction(db_session: AsyncSession) -> None:
    """Test policy restricts purchases to whitelisted categories only."""
    await PolicyService.configure_policy(
        session=db_session,
        user_id="user-cat-restricted",
        max_per_transaction_paise=100000,
        daily_limit_paise=200000,
        allowed_categories=[ProductCategory.SWEETS],  # Only sweets allowed!
    )

    # Attempt purchasing Food item
    res = await PolicyService.evaluate_policy(
        session=db_session,
        user_id="user-cat-restricted",
        category=ProductCategory.FOOD,
        amount_paise=2000,
    )

    assert res.is_allowed is False
    assert res.decision == "BLOCK"
    assert any("category_not_allowed" in r for r in res.violation_reasons)
