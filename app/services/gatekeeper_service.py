from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas import ProductSchema
from app.services.policy_service import PolicyEvaluationResult, PolicyService
from app.services.verification_service import VerificationService

logger = get_logger(__name__)


class GatekeeperDecision(BaseModel):
    """Authoritative decision from the combined pre-flight verification & policy gatekeeper."""
    is_authorized: bool
    decision: str = Field(description="'ALLOW', 'BLOCK', or 'PAUSED_STALE_STOCK'")
    verified_product: ProductSchema | None = None
    unit_price_inr: float
    total_amount_inr: float
    total_amount_paise: int
    verification_passed: bool
    policy_passed: bool
    blocked_reasons: list[str] = Field(default_factory=list)
    spent_today_inr: float = 0.0
    remaining_daily_budget_inr: float | None = None
    ping_id: str | None = None
    is_stale_paused: bool = False
    merchant_alerted: bool = False
    preflight_token: str | None = Field(default=None, description="Cryptographically signed single-use preflight token")


class GatekeeperService:
    """Atomic Pre-Flight Gatekeeper combining Authoritative Verification & Spending Policy Enforcement."""

    @staticmethod
    async def verify_and_authorize(
        session: AsyncSession,
        user_id: str,
        product_id: str,
        quantity: int = 1,
        user_max_price_paise: int | None = None,
        deadline_time: str | None = None,
    ) -> GatekeeperDecision:
        """Executes full atomic pre-flight checks: verifies product truth + enforces user spending limits."""
        logger.info(
            "Running pre-flight gatekeeper authorization",
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )

        # Step 1: Authoritative Product Verification
        v_result = await VerificationService.verify_product(
            session=session,
            product_id=product_id,
            requested_quantity=quantity,
            user_max_price_paise=user_max_price_paise,
            deadline_time=deadline_time,
        )

        all_blocked_reasons: list[str] = list(v_result.failure_reasons)
        policy_passed = False
        p_result: PolicyEvaluationResult | None = None

        # Step 2: User Spending Policy Evaluation (only if product exists)
        if v_result.product:
            p_result = await PolicyService.evaluate_policy(
                session=session,
                user_id=user_id,
                category=v_result.product.category,
                amount_paise=v_result.total_amount_paise,
            )
            policy_passed = p_result.is_allowed
            if not policy_passed:
                all_blocked_reasons.extend(p_result.violation_reasons)

        is_authorized = v_result.is_verified and policy_passed

        spent_today_inr = (p_result.spent_today_paise / 100) if p_result else 0.0
        rem_budget_inr = (
            (p_result.remaining_daily_budget_paise / 100)
            if p_result and p_result.remaining_daily_budget_paise is not None
            else None
        )

        if v_result.is_stale_paused:
            decision = "PAUSED_STALE_STOCK"
        elif is_authorized:
            decision = "ALLOW"
        else:
            decision = "BLOCK"

        preflight_token = None
        if is_authorized:
            preflight_token = GatekeeperService.generate_preflight_token(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                amount_paise=v_result.total_amount_paise,
            )

        return GatekeeperDecision(
            is_authorized=is_authorized,
            decision=decision,
            verified_product=v_result.product,
            unit_price_inr=v_result.unit_price_paise / 100,
            total_amount_inr=v_result.total_amount_paise / 100,
            total_amount_paise=v_result.total_amount_paise,
            verification_passed=v_result.is_verified,
            policy_passed=policy_passed,
            blocked_reasons=all_blocked_reasons,
            spent_today_inr=spent_today_inr,
            remaining_daily_budget_inr=rem_budget_inr,
            ping_id=v_result.ping_id,
            is_stale_paused=v_result.is_stale_paused,
            merchant_alerted=v_result.is_stale_paused,
            preflight_token=preflight_token,
        )

    @staticmethod
    def generate_preflight_token(
        user_id: str,
        product_id: str,
        quantity: int,
        amount_paise: int,
        ttl_seconds: int = 900,
    ) -> str:
        """Generates a cryptographically signed HMAC-SHA256 single-use preflight authorization token."""
        import base64
        import hashlib
        import hmac
        import json
        import time
        import uuid

        from app.core.config import get_settings

        settings = get_settings()
        secret = settings.JWT_SECRET_KEY or settings.RAZORPAY_KEY_SECRET

        payload = {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "amount_paise": amount_paise,
            "exp": int(time.time()) + ttl_seconds,
            "nonce": uuid.uuid4().hex[:12],
        }
        raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(raw_json).decode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{b64_payload}.{sig}"

    @staticmethod
    def verify_preflight_token(
        token: str,
        user_id: str,
        product_id: str,
        quantity: int,
    ) -> tuple[bool, str | None]:
        """Validates that a preflight token has a valid cryptographic signature,
        has not expired, and matches the requested transaction parameters.
        Returns (is_valid, error_reason)."""
        import base64
        import hashlib
        import hmac
        import json
        import time

        from app.core.config import get_settings

        if not token or "." not in token:
            return False, "Malformed preflight token format"

        b64_payload, sig = token.split(".", 1)
        settings = get_settings()
        secret = settings.JWT_SECRET_KEY or settings.RAZORPAY_KEY_SECRET

        expected_sig = hmac.new(secret.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, sig):
            return False, "Invalid cryptographic preflight signature (tampered)"

        try:
            payload_bytes = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return False, "Failed to decode preflight token payload"

        now = int(time.time())
        if data.get("exp", 0) < now:
            return False, f"Preflight token has expired (expired {now - data.get('exp', 0)}s ago)"

        if data.get("user_id") != user_id:
            return False, f"Token user mismatch (expected {user_id}, got {data.get('user_id')})"

        if data.get("product_id") != product_id:
            return False, f"Token product mismatch (expected {product_id}, got {data.get('product_id')})"

        if data.get("quantity") != quantity:
            return False, f"Token quantity mismatch (expected {quantity}, got {data.get('quantity')})"

        return True, None

