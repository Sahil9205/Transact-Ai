from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.products import get_vector_service_dep
from app.db.database import get_db
from app.domain.schemas import BuyerIntentSchema
from app.services.discovery_service import DiscoveryService, RankedCandidateSchema
from app.services.intent_service import IntentService
from app.services.vector_service import VectorService

router = APIRouter(prefix="/discovery", tags=["Discovery & Matching"])


class DiscoveryMatchRequest(BaseModel):
    """Request payload for multi-provider candidate discovery."""
    prompt: str | None = Field(
        default=None,
        examples=["Rasgulla under ₹500 in 110001", "Bengali sweets under 400"],
        description="Raw natural language prompt",
    )
    intent: BuyerIntentSchema | None = Field(
        default=None,
        description="Pre-structured BuyerIntentSchema (optional if prompt is provided)",
    )


class DiscoveryMatchResponse(BaseModel):
    """Ranked discovery search response."""
    parsed_intent: BuyerIntentSchema
    total_candidates: int
    candidates: list[RankedCandidateSchema]


@router.post(
    "/match",
    response_model=DiscoveryMatchResponse,
    summary="Multi-Provider Hybrid Matching & Ranking",
    description="Accepts raw natural language prompt or structured intent, performs hybrid semantic discovery across all connected merchants (local & quick-commerce), applies hard safety constraints, and returns deterministically ranked recommendations.",
)
async def match_candidates_endpoint(
    request: DiscoveryMatchRequest,
    session: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service_dep),
) -> DiscoveryMatchResponse:
    """Execute multi-provider hybrid candidate discovery and ranking."""
    if request.intent:
        intent = request.intent
    elif request.prompt:
        intent = IntentService.parse_intent(request.prompt)
    else:
        # Fallback empty intent
        intent = BuyerIntentSchema(product_query="")

    ranked_candidates = await DiscoveryService.match_candidates(
        session=session,
        intent=intent,
        vector_service=vector_service,
    )

    return DiscoveryMatchResponse(
        parsed_intent=intent,
        total_candidates=len(ranked_candidates),
        candidates=ranked_candidates,
    )
