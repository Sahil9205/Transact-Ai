from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, FulfillmentType, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.mcp.tools import MCP_TOOLS_DEFINITIONS, MCPCommerceTools
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_mcp_tool_definitions() -> None:
    """Test MCP tool definitions conform to MCP specification."""
    assert len(MCP_TOOLS_DEFINITIONS) == 7
    tool_names = [t["name"] for t in MCP_TOOLS_DEFINITIONS]
    assert "transact_discover_merchants" in tool_names
    assert "transact_search_catalog" in tool_names
    assert "transact_get_product" in tool_names
    assert "transact_check_availability" in tool_names
    assert "transact_get_merchant_manifest" in tool_names
    assert "transact_create_order_payment" in tool_names
    assert "transact_verify_order_preflight" in tool_names

    for tool in MCP_TOOLS_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


@pytest.mark.asyncio
async def test_mcp_commerce_tools_execution(db_session: AsyncSession) -> None:
    """Test execution of MCP tool handlers."""
    # 1. Onboard merchant & product
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(
            name="Sharma Sweets MCP",
            type=ProviderType.LOCAL_MERCHANT,
            pincode="110001",
        ),
    )
    product = await ProductService.add_product(
        db_session,
        merchant.provider_id,
        ProductCreateSchema(
            name="Sponge Rasgulla",
            category=ProductCategory.SWEETS,
            price_amount=45000,  # ₹450
            quantity=30,
            availability_status=AvailabilityStatus.IN_STOCK,
            fulfillment_type=FulfillmentType.PICKUP,
            prep_time_minutes=15,
            pincode="110001",
        ),
    )

    # 2. Test transact_discover_merchants
    discovery_res = await MCPCommerceTools.discover_merchants(
        session=db_session,
        pincode="110001",
    )
    assert discovery_res["total_found"] >= 1
    assert any(m["provider_id"] == merchant.provider_id for m in discovery_res["merchants"])

    # 3. Test transact_search_catalog
    search_res = await MCPCommerceTools.search_catalog(
        session=db_session,
        query="Rasgulla",
        max_price_inr=500.0,
    )
    assert search_res["total_matches"] >= 1
    assert search_res["products"][0]["name"] == "Sponge Rasgulla"
    assert search_res["products"][0]["price_inr"] == 450.0

    # Search with lower budget should filter it out
    low_budget_res = await MCPCommerceTools.search_catalog(
        session=db_session,
        query="Rasgulla",
        max_price_inr=300.0,
    )
    assert low_budget_res["total_matches"] == 0

    # 4. Test transact_get_product
    get_res = await MCPCommerceTools.get_product(
        session=db_session,
        product_id=product.product_id,
    )
    assert get_res["product_id"] == product.product_id
    assert get_res["price_inr"] == 450.0

    # 5. Test transact_check_availability
    avail_res = await MCPCommerceTools.check_availability(
        session=db_session,
        product_id=product.product_id,
    )
    assert avail_res["is_available"] is True
    assert avail_res["available_quantity"] == 30

    # 6. Test transact_get_merchant_manifest
    manifest_res = await MCPCommerceTools.get_merchant_manifest(
        session=db_session,
        merchant_id=merchant.provider_id,
    )
    assert manifest_res["provider_id"] == merchant.provider_id
    assert manifest_res["name"] == "Sharma Sweets MCP"

    # 7. Test transact_verify_order_preflight
    preflight_res = await MCPCommerceTools.verify_order_preflight(
        session=db_session,
        product_id=product.product_id,
        quantity=1,
    )
    assert preflight_res["is_authorized"] is True

    # 8. Test transact_create_order_payment
    order_res = await MCPCommerceTools.create_order_payment(
        session=db_session,
        product_id=product.product_id,
        quantity=1,
    )
    assert order_res["status"] == "payment_pending"
    assert order_res["amount_inr"] == 450.0
    assert "payment_link_url" in order_res
    assert order_res["payment_link_url"].startswith("http")

