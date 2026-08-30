from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import AuditEventModel
from app.db.repository import AuditRepository
from app.domain.enums import AuditEventType

logger = get_logger(__name__)


class AuditEventResponse(BaseModel):
    """Structured representation of an audit event from the ledger."""
    id: int
    event_type: str
    timestamp: datetime
    user_id: str | None = None
    provider_id: str | None = None
    product_id: str | None = None
    order_id: str | None = None
    amount_inr: float | None = None
    amount_paise: int | None = None
    reason: str | None = None
    result: str | None = None
    metadata: dict[str, Any] | None = None


class OrderTimelineResponse(BaseModel):
    """Chronological audit story for a specific order."""
    order_id: str
    total_events: int
    timeline: list[AuditEventResponse]


class AuditService:
    """Production 3-Layer Audit Trail Service (DB Ledger + Structured Logging + Observability)."""

    @staticmethod
    async def record_audit_event(
        session: AsyncSession,
        event_type: AuditEventType | str,
        user_id: str | None = None,
        provider_id: str | None = None,
        product_id: str | None = None,
        order_id: str | None = None,
        amount_paise: int | None = None,
        reason: str | None = None,
        result: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEventModel:
        """Records an event across all 3 audit layers (DB, Structlog, Observability)."""
        ev_type_str = event_type.value if isinstance(event_type, AuditEventType) else str(event_type)

        # Layer 1: Immutable Database Ledger
        event = await AuditRepository.log_event(
            session=session,
            event_type=ev_type_str,
            user_id=user_id,
            provider_id=provider_id,
            product_id=product_id,
            order_id=order_id,
            amount=amount_paise,
            reason=reason,
            result=result,
            metadata=metadata,
        )

        # Layer 2: Machine-readable Structured JSON Logs
        logger.info(
            "AUDIT_EVENT_EMITTED",
            event_id=event.id,
            event_type=ev_type_str,
            user_id=user_id,
            order_id=order_id,
            product_id=product_id,
            amount_paise=amount_paise,
            amount_inr=(amount_paise / 100) if amount_paise is not None else None,
            result=result,
            reason=reason,
            metadata=metadata,
        )

        return event

    @staticmethod
    async def query_audit_logs(
        session: AsyncSession,
        user_id: str | None = None,
        order_id: str | None = None,
        product_id: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEventResponse]:
        """Queries historical audit logs with flexible filtering and pagination."""
        stmt = select(AuditEventModel)

        if user_id:
            stmt = stmt.where(AuditEventModel.user_id == user_id)
        if order_id:
            stmt = stmt.where(AuditEventModel.order_id == order_id)
        if product_id:
            stmt = stmt.where(AuditEventModel.product_id == product_id)
        if event_type:
            stmt = stmt.where(AuditEventModel.event_type == event_type)

        stmt = stmt.order_by(desc(AuditEventModel.timestamp)).offset(offset).limit(limit)
        result = await session.execute(stmt)
        events = result.scalars().all()

        return [
            AuditEventResponse(
                id=e.id,
                event_type=e.event_type,
                timestamp=e.timestamp,
                user_id=e.user_id,
                provider_id=e.provider_id,
                product_id=e.product_id,
                order_id=e.order_id,
                amount_inr=(e.amount / 100) if e.amount is not None else None,
                amount_paise=e.amount,
                reason=e.reason,
                result=e.result,
                metadata=e.metadata_json,
            )
            for e in events
        ]

    @staticmethod
    async def get_order_timeline(session: AsyncSession, order_id: str) -> OrderTimelineResponse:
        """Reconstructs the chronological audit timeline for a specific order."""
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.order_id == order_id)
            .order_by(AuditEventModel.timestamp.asc())
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

        timeline = [
            AuditEventResponse(
                id=e.id,
                event_type=e.event_type,
                timestamp=e.timestamp,
                user_id=e.user_id,
                provider_id=e.provider_id,
                product_id=e.product_id,
                order_id=e.order_id,
                amount_inr=(e.amount / 100) if e.amount is not None else None,
                amount_paise=e.amount,
                reason=e.reason,
                result=e.result,
                metadata=e.metadata_json,
            )
            for e in events
        ]

        return OrderTimelineResponse(
            order_id=order_id,
            total_events=len(timeline),
            timeline=timeline,
        )
