from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AuditEventType
from app.services.audit_service import AuditService


@pytest.mark.asyncio
async def test_audit_recording_and_querying(db_session: AsyncSession) -> None:
    """Test recording events and querying the immutable audit ledger."""
    user_id = "audit-user-1"
    order_id = "order-audit-test-101"

    # 1. Record multiple lifecycle events
    await AuditService.record_audit_event(
        session=db_session,
        event_type=AuditEventType.INTENT_RECEIVED,
        user_id=user_id,
        order_id=order_id,
        amount_paise=50000,
        reason="User requested 1kg Rasgulla",
    )
    await AuditService.record_audit_event(
        session=db_session,
        event_type=AuditEventType.VERIFICATION_PASSED,
        user_id=user_id,
        order_id=order_id,
        amount_paise=45000,
        result="PASSED",
        reason="Stock and price verified",
    )
    await AuditService.record_audit_event(
        session=db_session,
        event_type=AuditEventType.PAYMENT_SUCCESS,
        user_id=user_id,
        order_id=order_id,
        amount_paise=45000,
        result="SUCCESS",
        reason="Payment settled via Razorpay",
    )

    # 2. Query audit logs by order_id
    events = await AuditService.query_audit_logs(
        session=db_session,
        order_id=order_id,
    )
    assert len(events) == 3
    assert events[0].order_id == order_id

    # 3. Query audit logs by event_type
    intent_events = await AuditService.query_audit_logs(
        session=db_session,
        event_type=AuditEventType.INTENT_RECEIVED.value,
    )
    assert len(intent_events) >= 1
    assert intent_events[0].amount_inr == 500.0

    # 4. Get chronological timeline
    timeline_res = await AuditService.get_order_timeline(
        session=db_session,
        order_id=order_id,
    )
    assert timeline_res.order_id == order_id
    assert timeline_res.total_events == 3
    # Chronological: first event should be INTENT_RECEIVED
    assert timeline_res.timeline[0].event_type == AuditEventType.INTENT_RECEIVED.value
    assert timeline_res.timeline[-1].event_type == AuditEventType.PAYMENT_SUCCESS.value
