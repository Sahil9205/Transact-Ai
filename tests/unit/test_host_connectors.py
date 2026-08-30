from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.external_host_service import ExternalHostService
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService


def test_host_tool_schemas_formats() -> None:
    """Test tool schema exports for Gemini, OpenAI, and Anthropic."""
    # 1. Gemini Format
    gemini_tools = ExternalHostService.get_host_tools_schema(format="gemini")
    assert len(gemini_tools) == 6
    assert all("name" in t and "parameters" in t for t in gemini_tools)

    # 2. OpenAI Format
    openai_tools = ExternalHostService.get_host_tools_schema(format="openai")
    assert len(openai_tools) == 6
    assert all(t["type"] == "function" and "function" in t for t in openai_tools)

    # 3. Anthropic Format
    anthropic_tools = ExternalHostService.get_host_tools_schema(format="anthropic")
    assert len(anthropic_tools) == 6
    assert all("input_schema" in t for t in anthropic_tools)


@pytest.mark.asyncio
async def test_universal_tool_execution_dispatcher(db_session: AsyncSession) -> None:
    """Test external tool dispatcher executing search, preflight, and payment creation."""
    # 1. Onboard merchant and product
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Host Sweets Store", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Host Special Rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=40000,  # ₹400
            quantity=20,
            availability_status=AvailabilityStatus.IN_STOCK,
            pincode="110001",
        ),
    )

    user_id = "external-host-test-user"

    # 2. Dispatch 'search_products'
    search_res = await ExternalHostService.dispatch_tool_call(
        session=db_session,
        tool_name="search_products",
        arguments={"query": "Rasgulla", "max_price_inr": 500, "pincode": "110001"},
        user_id=user_id,
    )
    assert search_res["success"] is True
    assert search_res["total_matches"] >= 1

    # 3. Dispatch 'get_product_details'
    details_res = await ExternalHostService.dispatch_tool_call(
        session=db_session,
        tool_name="get_product_details",
        arguments={"product_id": product.product_id},
        user_id=user_id,
    )
    assert details_res["success"] is True
    assert details_res["product"]["name"] == "Host Special Rasgulla"

    # 4. Dispatch 'verify_order_preflight'
    verify_res = await ExternalHostService.dispatch_tool_call(
        session=db_session,
        tool_name="verify_order_preflight",
        arguments={"user_id": user_id, "product_id": product.product_id, "quantity": 1},
        user_id=user_id,
    )
    assert verify_res["success"] is True
    assert verify_res["gatekeeper_decision"]["is_authorized"] is True

    # 5. Dispatch 'create_payment_order'
    pay_res = await ExternalHostService.dispatch_tool_call(
        session=db_session,
        tool_name="create_payment_order",
        arguments={"user_id": user_id, "product_id": product.product_id, "quantity": 1},
        user_id=user_id,
    )
    assert pay_res["success"] is True
    assert pay_res["payment_order"]["amount_inr"] == 400.0
    order_id = pay_res["payment_order"]["order_id"]

    # 6. Dispatch 'get_order_timeline'
    timeline_res = await ExternalHostService.dispatch_tool_call(
        session=db_session,
        tool_name="get_order_timeline",
        arguments={"order_id": order_id},
        user_id=user_id,
    )
    assert timeline_res["success"] is True
    assert timeline_res["order_timeline"]["total_events"] >= 1

    # 7. Dispatch 'find_smart_alternatives'
    alts_res = await ExternalHostService.dispatch_tool_call(
        session=db_session,
        tool_name="find_smart_alternatives",
        arguments={"product_query": "Motichoor Ladoo", "max_price_inr": 300, "pincode": "110001"},
        user_id=user_id,
    )
    assert alts_res["success"] is True
