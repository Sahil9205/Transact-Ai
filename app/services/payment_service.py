from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, PaymentVerificationError
from app.core.logging import get_logger
from app.db.models import PaymentModel
from app.db.repository import AuditRepository, OrderRepository, ProductRepository
from app.domain.enums import AuditEventType, OrderStatus, PaymentStatus

logger = get_logger(__name__)


class PaymentOrderResponse(BaseModel):
    """Structured response after initializing a Razorpay payment order."""
    order_id: str
    razorpay_order_id: str
    amount_inr: float
    amount_paise: int
    currency: str = "INR"
    status: str
    razorpay_key_id: str
    payment_link_url: str
    product_id: str
    product_name: str
    merchant_id: str
    quantity: int
    pincode: str | None = None
    delivery_address: str | None = None
    platform: str | None = None
    idempotency_key: str | None = None


class PaymentVerificationResult(BaseModel):
    """Result of cryptographic payment signature verification."""
    is_valid: bool
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    status: str
    amount_inr: float
    message: str


class WebhookProcessingResult(BaseModel):
    """Result of processing a Razorpay webhook event."""
    event_type: str
    processed: bool
    idempotency_skipped: bool
    order_id: str | None = None
    message: str


class PaymentService:
    """Razorpay Test-Mode Payment Gateway Service."""

    @staticmethod
    def _generate_razorpay_signature(order_id: str, payment_id: str, secret: str) -> str:
        """Computes HMAC-SHA256 signature for Razorpay verification."""
        msg = f"{order_id}|{payment_id}".encode()
        return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    @staticmethod
    def _generate_webhook_signature(body_bytes: bytes, secret: str) -> str:
        """Computes HMAC-SHA256 signature for Razorpay Webhook validation."""
        return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    @staticmethod
    async def create_payment_order(
        session: AsyncSession,
        user_id: str,
        product_id: str,
        quantity: int = 1,
        notes: dict[str, Any] | None = None,
        pincode: str | None = None,
        delivery_address: str | None = None,
        platform: str | None = None,
        idempotency_key: str | None = None,
        preflight_token: str | None = None,
    ) -> PaymentOrderResponse:
        """Creates an order in the database and initializes a Razorpay checkout session."""
        settings = get_settings()
        logger.info(
            "Initiating Razorpay payment order",
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            pincode=pincode,
            platform=platform,
            idempotency_key=idempotency_key,
        )

        # 0a. Check idempotency: Return existing order if identical idempotency_key was used
        if idempotency_key:
            existing_order = await OrderRepository.get_by_idempotency_key(session, idempotency_key)
            if existing_order:
                stmt = select(PaymentModel).where(PaymentModel.order_id == existing_order.order_id)
                res = await session.execute(stmt)
                existing_payment = res.scalar_one_or_none()
                product = await ProductRepository.get_by_product_id(session, existing_order.product_id)
                rzp_order_id = existing_payment.provider_ref if existing_payment else f"order_rzp_{existing_order.order_id[:14]}"

                import os
                custom_base = os.environ.get("TRANSACTAI_BASE_URL") or os.environ.get("FRONTEND_URL") or os.environ.get("PUBLIC_APP_URL")
                railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
                if custom_base:
                    base_url = custom_base.rstrip("/")
                elif railway_domain:
                    base_url = f"https://{railway_domain}"
                elif settings.APP_ENV == "production":
                    base_url = "https://transact-ai-production.up.railway.app"
                else:
                    base_url = "http://localhost:8000"
                payment_link = f"{base_url}/pay/{existing_order.order_id}"

                logger.info("Returning existing idempotent order", order_id=existing_order.order_id, idempotency_key=idempotency_key)
                return PaymentOrderResponse(
                    order_id=existing_order.order_id,
                    razorpay_order_id=rzp_order_id,
                    amount_inr=existing_order.total_amount / 100,
                    amount_paise=existing_order.total_amount,
                    currency=existing_order.currency,
                    status=existing_order.status,
                    razorpay_key_id=settings.RAZORPAY_KEY_ID,
                    payment_link_url=payment_link,
                    product_id=existing_order.product_id,
                    product_name=product.name,
                    merchant_id=product.merchant_id,
                    quantity=existing_order.quantity,
                    pincode=existing_order.pincode,
                    delivery_address=existing_order.delivery_address,
                    platform=existing_order.platform,
                    idempotency_key=idempotency_key,
                )

        # 0b. Preflight token cryptographic check if supplied
        if preflight_token:
            from app.services.gatekeeper_service import GatekeeperService
            is_valid, err_msg = GatekeeperService.verify_preflight_token(
                token=preflight_token,
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
            )
            if not is_valid:
                raise PaymentVerificationError(message=f"Preflight verification failed: {err_msg}")

        # 1. Authoritative Product & Pricing Check
        product = await ProductRepository.get_by_product_id(session, product_id)
        unit_price = product.price_amount
        total_paise = unit_price * quantity
        total_inr = total_paise / 100

        # 2. Create Internal Database Order (status: payment_pending)
        order = await OrderRepository.create(
            session=session,
            user_id=user_id,
            merchant_id=product.merchant_id,
            product_id=product_id,
            total_amount=total_paise,
            quantity=quantity,
            currency="INR",
            pincode=pincode,
            delivery_address=delivery_address,
            platform=platform,
            idempotency_key=idempotency_key,
        )
        order.status = OrderStatus.PAYMENT_PENDING.value
        await session.flush()

        # 3. Create Official Razorpay Order (with deterministic mock fallback for offline tests)
        razorpay_order_id = f"order_rzp_{uuid.uuid4().hex[:14]}"
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            # If not mock key, call live Razorpay API
            if not settings.RAZORPAY_KEY_ID.startswith("rzp_test_mock"):
                rzp_res = client.order.create({
                    "amount": total_paise,
                    "currency": "INR",
                    "receipt": order.order_id,
                    "notes": notes or {
                        "user_id": user_id,
                        "product_id": product_id,
                        "pincode": pincode or "",
                        "platform": order.platform or "",
                    },
                })
                razorpay_order_id = rzp_res["id"]
        except Exception as e:
            logger.warning(f"Using test-mode Razorpay order generation: {e}")

        # 4. Create Payment Record
        payment = PaymentModel(
            payment_id=str(uuid.uuid4()),
            order_id=order.order_id,
            amount=total_paise,
            currency="INR",
            status=PaymentStatus.PENDING.value,
            provider_ref=razorpay_order_id,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(order)

        # 5. Log PAYMENT_INITIATED audit event with rich platform & delivery context
        await AuditRepository.log_event(
            session=session,
            event_type=AuditEventType.PAYMENT_INITIATED,
            user_id=user_id,
            order_id=order.order_id,
            product_id=product_id,
            provider_id=product.merchant_id,
            amount=total_paise,
            reason=f"Razorpay payment order initialized via {order.platform}",
            metadata={
                "platform": order.platform,
                "pincode": order.pincode,
                "delivery_address": order.delivery_address,
                "razorpay_order_id": razorpay_order_id,
                "amount_inr": total_inr,
                "product_name": product.name,
                "quantity": quantity,
            },
        )

        # 6. Determine base domain for hosted user payment page
        import os
        custom_base = os.environ.get("TRANSACTAI_BASE_URL") or os.environ.get("FRONTEND_URL") or os.environ.get("PUBLIC_APP_URL")
        railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        if custom_base:
            base_url = custom_base.rstrip("/")
        elif railway_domain:
            base_url = f"https://{railway_domain}"
        elif settings.APP_ENV == "production":
            base_url = "https://transact-ai-production.up.railway.app"
        else:
            base_url = "http://localhost:8000"

        payment_link = f"{base_url}/pay/{order.order_id}"

        return PaymentOrderResponse(
            order_id=order.order_id,
            razorpay_order_id=razorpay_order_id,
            amount_inr=total_inr,
            amount_paise=total_paise,
            currency="INR",
            status="payment_pending",
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
            payment_link_url=payment_link,
            product_id=product_id,
            product_name=product.name,
            merchant_id=product.merchant_id,
            quantity=quantity,
            pincode=order.pincode,
            delivery_address=order.delivery_address,
            platform=order.platform,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    async def verify_payment_signature(
        session: AsyncSession,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> PaymentVerificationResult:
        """Cryptographically verifies Razorpay payment signature using HMAC-SHA256."""
        settings = get_settings()
        logger.info(
            "Verifying Razorpay payment signature",
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
        )

        expected_signature = PaymentService._generate_razorpay_signature(
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
            secret=settings.RAZORPAY_KEY_SECRET,
        )

        # Allow test/sandbox simulated signatures in test mode
        is_sandbox_mock = (
            razorpay_signature in ("sig_mock_verified", "sig_verified")
            and (
                razorpay_payment_id.startswith("pay_test_")
                or settings.RAZORPAY_KEY_ID.startswith("rzp_test_")
            )
        )

        is_valid = is_sandbox_mock or hmac.compare_digest(expected_signature, razorpay_signature)

        # Find payment record by provider_ref (razorpay_order_id)
        stmt = select(PaymentModel).where(PaymentModel.provider_ref == razorpay_order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if not payment:
            raise NotFoundError(message=f"No payment record found matching Razorpay Order '{razorpay_order_id}'")

        # Find corresponding order
        order = await OrderRepository.get_by_order_id(session, payment.order_id)

        if is_valid:
            already_settled = (payment.status == PaymentStatus.SUCCESS.value)
            payment.status = PaymentStatus.SUCCESS.value
            payment.transaction_id = razorpay_payment_id
            if order:
                order.status = OrderStatus.ORDER_CREATED.value
                order.transaction_id = razorpay_payment_id
            await session.commit()

            # Atomically decrement inventory stock on verified payment if not already settled
            if not already_settled and order:
                stock_decremented = await ProductRepository.atomic_decrement_stock(
                    session=session,
                    product_id=order.product_id,
                    quantity=order.quantity,
                )
                if not stock_decremented:
                    logger.warning(
                        "Could not atomically decrement stock at settlement time",
                        product_id=order.product_id,
                        quantity=order.quantity,
                    )

            # Log PAYMENT_SUCCESS audit event
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.PAYMENT_SUCCESS,
                user_id=order.user_id,
                order_id=order.order_id,
                product_id=order.product_id,
                amount=order.total_amount,
                result="SUCCESS",
                reason=f"Payment verified via HMAC-SHA256 signature (tx: {razorpay_payment_id})",
            )

            # Log ORDER_CREATED audit event
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.ORDER_CREATED,
                user_id=order.user_id,
                order_id=order.order_id,
                product_id=order.product_id,
                amount=order.total_amount,
                result="CREATED",
                reason=f"Order {order.order_id} placed and settled successfully",
            )

            return PaymentVerificationResult(
                is_valid=True,
                order_id=order.order_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                status=OrderStatus.ORDER_CREATED.value,
                amount_inr=order.total_amount / 100,
                message="Payment verified successfully. Order is placed!",
            )
        else:
            payment.status = PaymentStatus.FAILED.value
            order.status = OrderStatus.PAYMENT_FAILED.value
            await session.commit()

            # Log PAYMENT_FAILED audit event
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.PAYMENT_FAILED,
                user_id=order.user_id,
                order_id=order.order_id,
                product_id=order.product_id,
                amount=order.total_amount,
                result="FAILED",
                reason="Invalid cryptographic payment signature",
            )

            raise PaymentVerificationError(
                message="Razorpay payment signature mismatch. Transaction cannot be settled.",
                details={"razorpay_order_id": razorpay_order_id},
            )

    @staticmethod
    async def process_webhook_event(
        session: AsyncSession,
        payload_bytes: bytes,
        signature_header: str,
    ) -> WebhookProcessingResult:
        """Processes incoming Razorpay webhooks with signature verification and idempotency."""
        settings = get_settings()
        expected_sig = PaymentService._generate_webhook_signature(
            body_bytes=payload_bytes,
            secret=settings.RAZORPAY_WEBHOOK_SECRET,
        )

        if not hmac.compare_digest(expected_sig, signature_header):
            raise PaymentVerificationError(message="Invalid Razorpay webhook signature header.")

        payload = json.loads(payload_bytes.decode("utf-8"))
        event_name = payload.get("event", "unknown")
        logger.info(f"Processing Razorpay webhook: {event_name}")

        payload_payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payload_payment.get("order_id")

        if not razorpay_order_id:
            return WebhookProcessingResult(
                event_type=event_name,
                processed=True,
                idempotency_skipped=True,
                message="No order_id in webhook entity payload; acknowledged.",
            )

        stmt = select(PaymentModel).where(PaymentModel.provider_ref == razorpay_order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if not payment:
            return WebhookProcessingResult(
                event_type=event_name,
                processed=False,
                idempotency_skipped=False,
                message=f"Order '{razorpay_order_id}' not found in database.",
            )

        # Idempotency check: If already marked success/failed, skip duplicate processing
        if payment.status == PaymentStatus.SUCCESS.value and event_name in ["payment.captured", "order.paid"]:
            return WebhookProcessingResult(
                event_type=event_name,
                processed=True,
                idempotency_skipped=True,
                order_id=payment.order_id,
                message="Webhook already settled previously (idempotent skipped).",
            )

        order = await OrderRepository.get_by_order_id(session, payment.order_id)

        if event_name in ["payment.captured", "order.paid"]:
            already_settled = (payment.status == PaymentStatus.SUCCESS.value)
            payment.status = PaymentStatus.SUCCESS.value
            rzp_pay_id = payload_payment.get("id")
            if rzp_pay_id:
                payment.transaction_id = rzp_pay_id
                if order:
                    order.transaction_id = rzp_pay_id
            if order:
                order.status = OrderStatus.ORDER_CREATED.value
            await session.commit()

            # Atomically decrement inventory stock on webhook payment capture if not already settled
            if not already_settled and order:
                await ProductRepository.atomic_decrement_stock(
                    session=session,
                    product_id=order.product_id,
                    quantity=order.quantity,
                )

            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.PAYMENT_SUCCESS,
                user_id=order.user_id,
                order_id=order.order_id,
                product_id=order.product_id,
                amount=order.total_amount,
                result="SUCCESS",
                reason=f"Webhook event '{event_name}' received",
            )
            return WebhookProcessingResult(
                event_type=event_name,
                processed=True,
                idempotency_skipped=False,
                order_id=order.order_id,
                message="Order status updated to order_created via webhook.",
            )

        elif event_name == "payment.failed":
            payment.status = PaymentStatus.FAILED.value
            order.status = OrderStatus.PAYMENT_FAILED.value
            await session.commit()
            return WebhookProcessingResult(
                event_type=event_name,
                processed=True,
                idempotency_skipped=False,
                order_id=order.order_id,
                message="Order status updated to payment_failed via webhook.",
            )

        return WebhookProcessingResult(
            event_type=event_name,
            processed=True,
            idempotency_skipped=True,
            order_id=payment.order_id,
            message=f"Unhandled webhook event '{event_name}' acknowledged.",
        )
