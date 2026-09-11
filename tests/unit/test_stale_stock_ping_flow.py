from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MerchantModel, ProductModel
from app.db.repository import ProductRepository
from app.domain.enums import AvailabilityStatus, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, StockPingConfirmRequest
from app.services.gatekeeper_service import GatekeeperService
from app.services.stock_ping_service import StockPingService


@pytest.mark.asyncio
async def test_stale_stock_6h_guardrail_and_ping_resolution_flow(db_session: AsyncSession):
    """End-to-End Simulation:
    1. Fresh product passes preflight.
    2. Simulates product stock > 6 hours old (7 hours).
    3. Verifies AI preflight pauses checkout (PAUSED_STALE_STOCK) and dispatches merchant ping.
    4. Verifies merchant dashboard fetches the pending ping.
    5. Merchant clicks 'Confirm In Stock'.
    6. Verifies AI preflight resolves to ALLOW (checkout unblocked).
    """
    # Step 0: Setup merchant and product in database
    merchant = MerchantModel(
        name="Aggarwal Kirana Store",
        type=ProviderType.LOCAL_MERCHANT.value,
        contact_email="aggarwal@test.com",
        contact_phone="+919811223344",
        business_type="kirana",
        location="Chandni Chowk, Delhi",
        pincode="110006",
    )
    db_session.add(merchant)
    await db_session.flush()
    await db_session.refresh(merchant)

    product_data = ProductCreateSchema(
        name="Tata Salt 1kg",
        category=ProductCategory.GROCERIES,
        price_amount=2800,  # ₹28.00 in paise
        unit="pack",
        quantity=50,
        availability_status=AvailabilityStatus.IN_STOCK,
        pincode="110006",
    )
    product = await ProductRepository.create(db_session, merchant.merchant_id, product_data)

    # Step 1: Normal fresh product passes preflight
    decision_fresh = await GatekeeperService.verify_and_authorize(
        session=db_session,
        user_id="user_test_buyer",
        product_id=product.product_id,
        quantity=2,
    )
    assert decision_fresh.is_authorized is True
    assert decision_fresh.decision == "ALLOW"
    assert decision_fresh.is_stale_paused is False

    # Step 2: Simulate product with last_stock_updated_at > 6 hours ago (7 hours ago)
    seven_hours_ago = datetime.now(timezone.utc) - timedelta(hours=7)
    product.last_stock_updated_at = seven_hours_ago
    product.last_verified = seven_hours_ago
    await db_session.flush()
    await db_session.refresh(product)

    # Step 3: Trigger preflight verification on the stale product
    decision_stale = await GatekeeperService.verify_and_authorize(
        session=db_session,
        user_id="user_test_buyer",
        product_id=product.product_id,
        quantity=2,
    )
    assert decision_stale.is_authorized is False
    assert decision_stale.decision == "PAUSED_STALE_STOCK"
    assert decision_stale.is_stale_paused is True
    assert decision_stale.merchant_alerted is True
    assert decision_stale.ping_id is not None
    ping_id = decision_stale.ping_id

    # Step 4: Verify merchant can fetch the pending ping from their dashboard
    pings = await StockPingService.list_merchant_pings(
        session=db_session,
        merchant_id=merchant.merchant_id,
        status="pending",
    )
    assert len(pings) >= 1
    target_ping = next((p for p in pings if p.ping_id == ping_id), None)
    assert target_ping is not None
    assert target_ping.product_name == "Tata Salt 1kg"
    assert target_ping.requested_quantity == 2
    assert target_ping.status == "pending"

    # Step 5: Merchant clicks 'Confirm In Stock'
    confirm_res = await StockPingService.confirm_ping(
        session=db_session,
        merchant_id=merchant.merchant_id,
        ping_id=ping_id,
        available=True,
        new_quantity=45,
        notes="Fresh shipment arrived this afternoon",
    )
    assert confirm_res.status == "confirmed"
    assert confirm_res.resolved_at is not None

    # Verify product timestamp was refreshed in DB
    refreshed_prod = await ProductRepository.get_by_product_id(db_session, product.product_id)
    last_dt = refreshed_prod.last_stock_updated_at
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    time_diff = datetime.now(timezone.utc) - last_dt
    assert time_diff.total_seconds() < 60  # Updated within last minute
    assert refreshed_prod.quantity == 45

    # Step 6: Buyer / AI Agent re-verifies preflight ➔ Now passes cleanly!
    decision_resolved = await GatekeeperService.verify_and_authorize(
        session=db_session,
        user_id="user_test_buyer",
        product_id=product.product_id,
        quantity=2,
    )
    assert decision_resolved.is_authorized is True
    assert decision_resolved.decision == "ALLOW"
    assert decision_resolved.is_stale_paused is False
    assert decision_resolved.total_amount_inr == 56.0  # 2 * ₹28.00


@pytest.mark.asyncio
async def test_store_pulse_heartbeat_bulk_refresh(db_session: AsyncSession):
    """Verify 1-tap Store Pulse re-verifies all products and resolves pending pings."""
    merchant = MerchantModel(
        name="Daily Needs Store",
        type=ProviderType.LOCAL_MERCHANT.value,
        contact_email="dailyneeds@test.com",
    )
    db_session.add(merchant)
    await db_session.flush()

    eight_hours_ago = datetime.now(timezone.utc) - timedelta(hours=8)

    # Add 3 products, all stale
    p1 = await ProductRepository.create(
        db_session,
        merchant.merchant_id,
        ProductCreateSchema(name="Milk 500ml", category=ProductCategory.GROCERIES, price_amount=3000),
    )
    p2 = await ProductRepository.create(
        db_session,
        merchant.merchant_id,
        ProductCreateSchema(name="Bread White", category=ProductCategory.GROCERIES, price_amount=4000),
    )
    p1.last_stock_updated_at = eight_hours_ago
    p1.last_verified = eight_hours_ago
    p2.last_stock_updated_at = eight_hours_ago
    p2.last_verified = eight_hours_ago
    await db_session.flush()

    # Create a pending ping for p1
    ping = await StockPingService.create_or_get_pending_ping(
        session=db_session,
        merchant_id=merchant.merchant_id,
        product_id=p1.product_id,
    )
    assert ping.status == "pending"

    # Execute 1-tap Store Pulse
    refreshed_count = await StockPingService.store_pulse(db_session, merchant.merchant_id)
    assert refreshed_count >= 2

    # Verify both products are now fresh
    p1_fresh = await ProductRepository.get_by_product_id(db_session, p1.product_id)
    p1_dt = p1_fresh.last_stock_updated_at
    if p1_dt.tzinfo is None:
        p1_dt = p1_dt.replace(tzinfo=timezone.utc)
    assert (datetime.now(timezone.utc) - p1_dt).total_seconds() < 60

    # Verify pending ping was auto-confirmed
    pings = await StockPingService.list_merchant_pings(db_session, merchant.merchant_id)
    target = next(p for p in pings if p.ping_id == ping.ping_id)
    assert target.status == "confirmed"
