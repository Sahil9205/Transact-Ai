from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import OrderModel, SpendingPolicyModel, UserModel
from app.db.repository import AuditRepository
from app.domain.enums import AuditEventType, OrderStatus, ProductCategory
from app.domain.schemas import SpendingPolicySchema

logger = get_logger(__name__)


class PolicyEvaluationResult(BaseModel):
    """Structured evaluation output of user spending policy check."""
    is_allowed: bool
    decision: str = Field(description="'ALLOW' or 'BLOCK'")
    violation_reasons: list[str] = Field(default_factory=list)
    spent_today_paise: int = 0
    daily_limit_paise: int | None = None
    remaining_daily_budget_paise: int | None = None
    max_per_transaction_paise: int | None = None


class PolicyService:
    """Deterministic User Spending Policy Engine."""

    @staticmethod
    async def get_or_create_user(session: AsyncSession, user_id: str, name: str = "Demo Buyer") -> UserModel:
        """Ensures a user record exists in the database."""
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = UserModel(user_id=user_id, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    @staticmethod
    async def configure_policy(
        session: AsyncSession,
        user_id: str,
        max_per_transaction_paise: int,
        daily_limit_paise: int,
        allowed_categories: list[ProductCategory] | None = None,
        is_active: bool = True,
    ) -> SpendingPolicySchema:
        """Creates or updates a user spending policy."""
        logger.info(
            "Configuring user spending policy",
            user_id=user_id,
            max_per_tx=max_per_transaction_paise,
            daily_limit=daily_limit_paise,
        )
        await PolicyService.get_or_create_user(session, user_id)

        stmt = select(SpendingPolicyModel).where(SpendingPolicyModel.user_id == user_id)
        result = await session.execute(stmt)
        policy = result.scalar_one_or_none()

        categories_list = [c.value if isinstance(c, ProductCategory) else str(c) for c in (allowed_categories or [])]

        if policy:
            policy.max_per_transaction = max_per_transaction_paise
            policy.daily_limit = daily_limit_paise
            policy.allowed_categories = categories_list
            policy.is_active = is_active
        else:
            policy = SpendingPolicyModel(
                user_id=user_id,
                max_per_transaction=max_per_transaction_paise,
                daily_limit=daily_limit_paise,
                allowed_categories=categories_list,
                is_active=is_active,
            )
            session.add(policy)

        await session.commit()
        await session.refresh(policy)

        return SpendingPolicySchema(
            user_id=policy.user_id,
            max_per_transaction=policy.max_per_transaction,
            daily_limit=policy.daily_limit,
            allowed_categories=[ProductCategory(c) for c in policy.allowed_categories if c in ProductCategory._value2member_map_],
            is_active=policy.is_active,
        )

    @staticmethod
    async def get_policy(session: AsyncSession, user_id: str) -> SpendingPolicySchema | None:
        """Retrieves active policy for a user if configured."""
        stmt = select(SpendingPolicyModel).where(SpendingPolicyModel.user_id == user_id)
        result = await session.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            return None

        return SpendingPolicySchema(
            user_id=policy.user_id,
            max_per_transaction=policy.max_per_transaction,
            daily_limit=policy.daily_limit,
            allowed_categories=[ProductCategory(c) for c in policy.allowed_categories if c in ProductCategory._value2member_map_],
            is_active=policy.is_active,
        )

    @staticmethod
    async def calculate_spent_today(session: AsyncSession, user_id: str) -> int:
        """Calculates cumulative spend by user today (excluding cancelled orders)."""
        now = datetime.now(timezone.utc)
        today_midnight = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

        stmt = select(func.sum(OrderModel.total_amount)).where(
            OrderModel.user_id == user_id,
            OrderModel.created_at >= today_midnight,
            OrderModel.status != OrderStatus.CANCELLED.value,
        )
        result = await session.execute(stmt)
        spent = result.scalar()
        return int(spent) if spent is not None else 0

    @staticmethod
    async def evaluate_policy(
        session: AsyncSession,
        user_id: str,
        category: ProductCategory | str,
        amount_paise: int,
    ) -> PolicyEvaluationResult:
        """Evaluates whether a purchase complies with user spending limits."""
        policy_schema = await PolicyService.get_policy(session, user_id)
        spent_today = await PolicyService.calculate_spent_today(session, user_id)

        # If no policy set, default to unconstrained / safe fallback (₹50,000 per tx, ₹100,000 daily)
        if not policy_schema or not policy_schema.is_active:
            return PolicyEvaluationResult(
                is_allowed=True,
                decision="ALLOW",
                violation_reasons=[],
                spent_today_paise=spent_today,
                daily_limit_paise=None,
                remaining_daily_budget_paise=None,
                max_per_transaction_paise=None,
            )

        cat_val = category.value if isinstance(category, ProductCategory) else str(category)
        violations: list[str] = []

        # 1. Per-Transaction Limit Check
        if amount_paise > policy_schema.max_per_transaction:
            violations.append(
                f"per_transaction_limit_exceeded (amount ₹{amount_paise / 100:.2f} > max allowed ₹{policy_schema.max_per_transaction / 100:.2f})"
            )

        # 2. Daily Cumulative Limit Check
        if (spent_today + amount_paise) > policy_schema.daily_limit:
            remaining = max(0, policy_schema.daily_limit - spent_today)
            violations.append(
                f"daily_spending_limit_exceeded (spent today ₹{spent_today / 100:.2f} + current ₹{amount_paise / 100:.2f} > daily limit ₹{policy_schema.daily_limit / 100:.2f}. Remaining daily budget: ₹{remaining / 100:.2f})"
            )

        # 3. Category Restriction Check
        if policy_schema.allowed_categories:
            allowed_values = [c.value for c in policy_schema.allowed_categories]
            if cat_val not in allowed_values:
                violations.append(
                    f"category_not_allowed (category '{cat_val}' is not in user whitelist: {allowed_values})"
                )

        is_allowed = len(violations) == 0
        remaining_budget = max(0, policy_schema.daily_limit - (spent_today + (amount_paise if is_allowed else 0)))

        # Log policy check audit event
        if is_allowed:
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.POLICY_CHECK_PASSED,
                user_id=user_id,
                amount=amount_paise,
                result="PASSED",
                reason=f"Spending policy checks passed for ₹{amount_paise / 100:.2f}",
            )
        else:
            await AuditRepository.log_event(
                session=session,
                event_type=AuditEventType.POLICY_CHECK_FAILED,
                user_id=user_id,
                amount=amount_paise,
                result="BLOCKED",
                reason="; ".join(violations),
            )

        return PolicyEvaluationResult(
            is_allowed=is_allowed,
            decision="ALLOW" if is_allowed else "BLOCK",
            violation_reasons=violations,
            spent_today_paise=spent_today,
            daily_limit_paise=policy_schema.daily_limit,
            remaining_daily_budget_paise=remaining_budget,
            max_per_transaction_paise=policy_schema.max_per_transaction,
        )
