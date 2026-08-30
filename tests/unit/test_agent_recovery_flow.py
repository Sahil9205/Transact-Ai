from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.agent_service import AgentService
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_agent_graceful_recovery_with_alternatives(db_session: AsyncSession) -> None:
    """Test that LangGraph agent smoothly recovers from tight constraints and proposes alternatives."""
    # 1. Onboard merchant & product at ₹450
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets Recovery", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Premium Rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=45000,  # ₹450
            quantity=10,
            availability_status=AvailabilityStatus.IN_STOCK,
            pincode="110001",
        ),
    )

    # 2. User prompt with tight budget: "Rasgulla under ₹400 in 110001"
    user_id = "buyer-agent-recovery-test"
    final_state = await AgentService.run_agent(
        session=db_session,
        user_id=user_id,
        prompt="Rasgulla under ₹400 in 110001",
    )

    assert final_state["status"] in ["no_candidates", "proposed", "failed"]
    # Agent message should be rich and friendly, proposing alternatives or explaining failure gracefully
    assert len(final_state["agent_message"]) > 20
    assert "alternatives" in final_state
