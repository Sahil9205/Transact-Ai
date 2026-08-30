from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from app.domain.schemas import BuyerIntentSchema
from app.services.intent_service import IntentService

router = APIRouter(prefix="/intent", tags=["Buyer Intent"])


class IntentParseRequest(BaseModel):
    """Request payload containing user natural language prompt."""
    prompt: str = Field(
        ...,
        examples=["1kg rasgulla chahiye under ₹500 by 6:30 PM in 110001", "samosa and sweet lassi for 4 people under 300"],
        description="Natural language commerce inquiry in English, Hindi, or Hinglish",
    )


@router.post(
    "/parse",
    response_model=BuyerIntentSchema,
    summary="Parse Natural Language Intent",
    description="Transforms unstructured English, Hindi, or Hinglish buyer prompt into a strictly typed BuyerIntentSchema.",
)
async def parse_intent_endpoint(
    request: IntentParseRequest,
) -> BuyerIntentSchema:
    """Parse unstructured prompt into structured commerce intent."""
    return IntentService.parse_intent(request.prompt)
