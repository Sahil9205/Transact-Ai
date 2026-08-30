from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, FulfillmentType, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.agent_service import AgentService
from app.services.merchant_service import MerchantService
from app.services.policy_service import PolicyService
from app.services.product_service import ProductService
from app.services.vector_service import VectorService


@pytest.mark.asyncio
async def test_langgraph_agent_full_success_workflow(db_session: AsyncSession) -> None:
    """Test full LangGraph state graph execution from prompt to verified proposal."""
    vector_service = VectorService(collection_name="test_agent_graph_coll")
    await vector_service.ensure_collection()

    # 1. Onboard Sharma Sweets with Rasgulla @ ₹450
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Traditional Rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=45000,  # ₹450
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=15,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # 2. Configure user policy
    user_id = "agent-test-user-1"
    await PolicyService.configure_policy(
        session=db_session,
        user_id=user_id,
        max_per_transaction_paise=100000,  # ₹1000
        daily_limit_paise=300000,          # ₹3000
    )

    # 3. Execute Agent LangGraph workflow
    prompt = "1kg Traditional Rasgulla chahiye under ₹500 in 110001"
    final_state = await AgentService.run_agent(
        session=db_session,
        user_id=user_id,
        prompt=prompt,
        vector_service=vector_service,
    )

    assert final_state["status"] == "proposed"
    assert final_state["order_proposal"] is not None
    assert final_state["order_proposal"].product_name == "Traditional Rasgulla"
    assert final_state["order_proposal"].total_amount_inr == 450.0
    assert final_state["order_proposal"].savings_vs_budget_inr == 50.0  # ₹500 - ₹450 = ₹50
    assert "🎉 Found the best option!" in final_state["agent_message"]
    assert len(final_state["step_history"]) >= 4

    # 4. Test User Confirmation
    conf_res = await AgentService.confirm_proposal(
        session=db_session,
        user_id=user_id,
        product_id=final_state["order_proposal"].product_id,
        total_amount_paise=final_state["order_proposal"].total_amount_paise,
        confirmed=True,
    )
    assert conf_res["confirmed"] is True
    assert conf_res["status"] == "payment_ready"


@pytest.mark.asyncio
async def test_langgraph_agent_budget_too_low_fails_gracefully(db_session: AsyncSession) -> None:
    """Test LangGraph routes to failure node when budget is impossibly low."""
    vector_service = VectorService(collection_name="test_agent_budget_coll")
    await vector_service.ensure_collection()

    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Kaju Katli",
            category=ProductCategory.SWEETS,
            price_amount=80000,  # ₹800
            quantity=10,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # User searches for ₹800 Kaju Katli with ₹100 budget
    prompt = "Kaju Katli under 100 in 110001"
    final_state = await AgentService.run_agent(
        session=db_session,
        user_id="user-low-budget",
        prompt=prompt,
        vector_service=vector_service,
    )

    assert final_state["status"] == "no_candidates"
    assert final_state["order_proposal"] is None
    assert ("match nahi mila" in final_state["agent_message"] or "couldn't find" in final_state["agent_message"])


@pytest.mark.asyncio
async def test_langgraph_agent_spending_policy_blocks_gracefully(db_session: AsyncSession) -> None:
    """Test LangGraph routes to blocked node when user spending policy is violated."""
    vector_service = VectorService(collection_name="test_agent_policy_coll")
    await vector_service.ensure_collection()

    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Luxury Sweet Hamper",
            category=ProductCategory.SWEETS,
            price_amount=150000,  # ₹1500
            quantity=10,
            pincode="110001",
        ),
        vector_service=vector_service,
    )

    # User policy strictly allows max ₹500 per transaction
    user_id = "user-strict-policy"
    await PolicyService.configure_policy(
        session=db_session,
        user_id=user_id,
        max_per_transaction_paise=50000,  # Max ₹500
        daily_limit_paise=100000,
    )

    prompt = "Luxury Sweet Hamper in 110001"
    final_state = await AgentService.run_agent(
        session=db_session,
        user_id=user_id,
        prompt=prompt,
        vector_service=vector_service,
    )

    assert final_state["status"] == "blocked"
    assert final_state["order_proposal"] is None
    assert ("proceed nahi ho sakta" in final_state["agent_message"] or "cannot proceed" in final_state["agent_message"])
    assert any("per_transaction_limit_exceeded" in e for e in final_state["error_details"])
