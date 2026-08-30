from __future__ import annotations

import hashlib
import hmac
import json
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import PaymentVerificationError
from app.domain.enums import AvailabilityStatus, FulfillmentType, OrderStatus, PaymentStatus, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_create_payment_order_and_signature_verification(db_session: AsyncSession) -> None:
    """Test full payment lifecycle: order creation -> HMAC-SHA256 signature verification -> order settled."""
    settings = get_settings()

    # 1. Onboard merchant & product @ ₹450
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Rasgulla Box",
            category=ProductCategory.SWEETS,
            price_amount=45000,  # ₹450
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
            pincode="110001",
        ),
    )

    # 2. Create Payment Order for 2 units (₹900 = 90000 paise)
    user_id = "buyer-test-payment-1"
    order_res = await PaymentService.create_payment_order(
        session=db_session,
        user_id=user_id,
        product_id=product.product_id,
        quantity=2,
    )

    assert order_res.amount_inr == 900.0
    assert order_res.amount_paise == 90000
    assert order_res.status == "payment_pending"
    assert order_res.quantity == 2
    assert "checkout.razorpay.com" in order_res.payment_link_url

    # 3. Simulate successful frontend checkout with valid cryptographic HMAC-SHA256 signature
    mock_payment_id = "pay_rzp_mock123456"
    msg = f"{order_res.razorpay_order_id}|{mock_payment_id}".encode("utf-8")
    valid_signature = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    verification_res = await PaymentService.verify_payment_signature(
        session=db_session,
        razorpay_order_id=order_res.razorpay_order_id,
        razorpay_payment_id=mock_payment_id,
        razorpay_signature=valid_signature,
    )

    assert verification_res.is_valid is True
    assert verification_res.status == OrderStatus.ORDER_CREATED.value
    assert verification_res.amount_inr == 900.0


@pytest.mark.asyncio
async def test_payment_signature_tampered_fails(db_session: AsyncSession) -> None:
    """Test that tampered payment signatures are strictly rejected."""
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
            price_amount=35000,
            quantity=10,
        ),
    )

    order_res = await PaymentService.create_payment_order(
        session=db_session,
        user_id="buyer-tamper-test",
        product_id=product.product_id,
        quantity=1,
    )

    # Attempt verification with bogus signature
    with pytest.raises(PaymentVerificationError):
        await PaymentService.verify_payment_signature(
            session=db_session,
            razorpay_order_id=order_res.razorpay_order_id,
            razorpay_payment_id="pay_fake_123",
            razorpay_signature="invalid_bogus_tampered_signature_hex",
        )


@pytest.mark.asyncio
async def test_webhook_processing_and_idempotency(db_session: AsyncSession) -> None:
    """Test Razorpay webhook event processing with signature verification and idempotency."""
    settings = get_settings()

    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Kaju Barfi",
            category=ProductCategory.SWEETS,
            price_amount=50000,
            quantity=15,
        ),
    )

    order_res = await PaymentService.create_payment_order(
        session=db_session,
        user_id="buyer-webhook-test",
        product_id=product.product_id,
        quantity=1,
    )

    # Construct webhook event payload
    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_hook_123",
                    "order_id": order_res.razorpay_order_id,
                    "amount": 50000,
                    "status": "captured",
                }
            }
        },
    }
    payload_bytes = json.dumps(webhook_payload).encode("utf-8")
    webhook_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    # 1. First webhook delivery
    hook_res_1 = await PaymentService.process_webhook_event(
        session=db_session,
        payload_bytes=payload_bytes,
        signature_header=webhook_signature,
    )
    assert hook_res_1.processed is True
    assert hook_res_1.idempotency_skipped is False
    assert hook_res_1.order_id == order_res.order_id

    # 2. Duplicate webhook delivery (Idempotent Test)
    hook_res_2 = await PaymentService.process_webhook_event(
        session=db_session,
        payload_bytes=payload_bytes,
        signature_header=webhook_signature,
    )
    assert hook_res_2.processed is True
    assert hook_res_2.idempotency_skipped is True
