from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.audit_service import AuditEventResponse, AuditService

router = APIRouter(prefix="/audit", tags=["Compliance & Audit Trail"])


@router.get(
    "/events",
    response_model=list[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Query Audit Ledger Events",
    description="Queries the immutable production audit ledger with flexible filtering by user_id, order_id, product_id, or event_type.",
)
async def query_audit_events_endpoint(
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    order_id: str | None = Query(default=None, description="Filter by order ID"),
    product_id: str | None = Query(default=None, description="Filter by product ID"),
    event_type: str | None = Query(default=None, description="Filter by AuditEventType"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> list[AuditEventResponse]:
    """Query audit events from the immutable database ledger."""
    return await AuditService.query_audit_logs(
        session=session,
        user_id=user_id,
        order_id=order_id,
        product_id=product_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
