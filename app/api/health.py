from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    environment: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Response model for readiness check."""
    status: str
    database: str
    timestamp: str
    error: str | None = None


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(UTC).isoformat()
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(session: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """Readiness check endpoint verifying database connection."""
    try:
        await session.execute(text("SELECT 1"))
        return ReadinessResponse(
            status="ready",
            database="connected",
            timestamp=datetime.now(UTC).isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e)
            }
        )


root_health_router = APIRouter(tags=["Health"])


@root_health_router.get("/healthz", response_model=HealthResponse, summary="Liveness Probe")
async def liveness_probe(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Kubernetes / Cloud-native liveness probe."""
    return await health_check(settings=settings)


@root_health_router.get("/readyz", response_model=ReadinessResponse, summary="Readiness Probe")
async def readiness_probe(session: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """Kubernetes / Cloud-native readiness probe."""
    return await readiness_check(session=session)

