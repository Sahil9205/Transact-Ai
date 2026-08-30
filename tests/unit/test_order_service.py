from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AvailabilityStatus, OrderStatus, ProductCategory, ProviderType
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_order_management_lifecycle_and_fulfillment(db_session: AsyncSession) -> None:
    """Test full order lifecycle: creation -> fulfillment update -> completion."""
    # 1. Onboard merchant & product
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets Order Hub", type=ProviderType.LOCAL_MERCHANT, pincode="110001"),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Milk Cake",
            category=ProductCategory.SWEETS,
            price_amount=40000,  # ₹400
            quantity=15,
            availability_status=AvailabilityStatus.IN_STOCK,
            pincode="110001",
        ),
    )

    user_id = "order-test-user-1"

    # 2. Create Order via PaymentService
    payment_order = await PaymentService.create_payment_order(
        session=db_session,
        user_id=user_id,
        product_id=product.product_id,
        quantity=1,
    )
    order_id = payment_order.order_id

    # 3. Get Order Details
    details = await OrderService.get_order_details(session=db_session, order_id=order_id)
    assert details.order_id == order_id
    assert details.product_name == "Milk Cake"
    assert details.merchant_name == "Sharma Sweets Order Hub"
    assert details.total_amount_inr == 400.0

    # 4. List User Orders
    user_orders = await OrderService.list_user_orders(session=db_session, user_id=user_id)
    assert len(user_orders) >= 1
    assert any(o.order_id == order_id for o in user_orders)

    # 5. List Merchant Orders
    merch_orders = await OrderService.list_merchant_orders(session=db_session, merchant_id=merchant.provider_id)
    assert len(merch_orders) >= 1

    # 6. Merchant updates status to READY_FOR_PICKUP
    updated_1 = await OrderService.update_fulfillment_status(
        session=db_session,
        order_id=order_id,
        merchant_id=merchant.provider_id,
        new_status=OrderStatus.READY_FOR_PICKUP,
    )
    assert updated_1.status == OrderStatus.READY_FOR_PICKUP.value

    # 7. Merchant marks COMPLETED
    updated_2 = await OrderService.update_fulfillment_status(
        session=db_session,
        order_id=order_id,
        merchant_id=merchant.provider_id,
        new_status=OrderStatus.COMPLETED,
    )
    assert updated_2.status == OrderStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_order_cancellation(db_session: AsyncSession) -> None:
    """Test user order cancellation flow."""
    merchant = await MerchantService.register_merchant(
        db_session,
        ProviderCreateSchema(name="Sharma Sweets Cancel Hub", type=ProviderType.LOCAL_MERCHANT),
    )
    product = await ProductService.add_product(
        session=db_session,
        merchant_id=merchant.provider_id,
        data=ProductCreateSchema(
            name="Besan Ladoo",
            category=ProductCategory.SWEETS,
            price_amount=30000,
            quantity=10,
        ),
    )

    user_id = "user-cancel-test"
    order_res = await PaymentService.create_payment_order(
        session=db_session,
        user_id=user_id,
        product_id=product.product_id,
        quantity=1,
    )

    # Cancel order
    cancelled_order = await OrderService.cancel_order(
        session=db_session,
        order_id=order_res.order_id,
        user_id=user_id,
        reason="Changed my mind",
    )
    assert cancelled_order.status == OrderStatus.CANCELLED.value
