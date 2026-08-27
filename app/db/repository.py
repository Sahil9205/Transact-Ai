from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    MerchantModel, ProductModel, OrderModel, AuditEventModel,
    UserModel, SpendingPolicyModel, PaymentModel
)
from app.domain.schemas import (
    ProviderCreateSchema, ProductCreateSchema, ProductUpdateSchema
)
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MerchantRepository:
    @staticmethod
    async def create(session: AsyncSession, data: ProviderCreateSchema) -> MerchantModel:
        merchant = MerchantModel(
            name=data.name,
            type=data.type.value,
            description=data.description,
            location=data.location,
            pincode=data.pincode,
        )
        session.add(merchant)
        await session.flush()
        await session.refresh(merchant)
        logger.info(f"Created merchant {merchant.merchant_id}")
        return merchant
    
    @staticmethod
    async def get_by_merchant_id(session: AsyncSession, merchant_id: str) -> MerchantModel:
        result = await session.execute(select(MerchantModel).where(MerchantModel.merchant_id == merchant_id))
        merchant = result.scalar_one_or_none()
        if not merchant:
            raise NotFoundError(message=f"Merchant {merchant_id} not found")
        return merchant
    
    @staticmethod
    async def list_active(session: AsyncSession) -> list[MerchantModel]:
        result = await session.execute(select(MerchantModel).where(MerchantModel.is_active == True))
        return list(result.scalars().all())


class ProductRepository:
    @staticmethod
    async def create(session: AsyncSession, merchant_id: str, data: ProductCreateSchema) -> ProductModel:
        product = ProductModel(
            merchant_id=merchant_id,
            name=data.name,
            description=data.description,
            category=data.category.value,
            price_amount=data.price_amount,
            price_currency=data.price_currency,
            quantity=data.quantity,
            availability_status=data.availability_status.value,
            fulfillment_type=data.fulfillment_type.value,
            prep_time_minutes=data.prep_time_minutes,
            slot_capacity=data.slot_capacity,
            pincode=data.pincode,
        )
        session.add(product)
        await session.flush()
        await session.refresh(product)
        logger.info(f"Created product {product.product_id} for merchant {merchant_id}")
        return product
    
    @staticmethod
    async def get_by_product_id(session: AsyncSession, product_id: str) -> ProductModel:
        result = await session.execute(select(ProductModel).where(ProductModel.product_id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundError(message=f"Product {product_id} not found")
        return product
    
    @staticmethod
    async def search(
        session: AsyncSession,
        query: str | None = None,
        category: str | None = None,
        pincode: str | None = None,
        merchant_id: str | None = None,
    ) -> list[ProductModel]:
        stmt = select(ProductModel)
        if query:
            stmt = stmt.where(ProductModel.name.ilike(f"%{query}%"))
        if category:
            stmt = stmt.where(ProductModel.category == category)
        if pincode:
            stmt = stmt.where(ProductModel.pincode == pincode)
        if merchant_id:
            stmt = stmt.where(ProductModel.merchant_id == merchant_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def update(session: AsyncSession, product_id: str, data: ProductUpdateSchema) -> ProductModel:
        product = await ProductRepository.get_by_product_id(session, product_id)
        update_data = data.model_dump(exclude_unset=True)
        # Convert enum values to strings
        if 'availability_status' in update_data and update_data['availability_status'] is not None:
            update_data['availability_status'] = update_data['availability_status'].value
        for key, value in update_data.items():
            setattr(product, key, value)
        product.last_verified = datetime.now(timezone.utc)
        await session.flush()
        await session.refresh(product)
        logger.info(f"Updated product {product.product_id}")
        return product


class OrderRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: str,
        merchant_id: str,
        product_id: str,
        total_amount: int,
        quantity: int = 1,
        currency: str = "INR"
    ) -> OrderModel:
        order = OrderModel(
            user_id=user_id,
            merchant_id=merchant_id,
            product_id=product_id,
            quantity=quantity,
            total_amount=total_amount,
            currency=currency,
        )
        session.add(order)
        await session.flush()
        await session.refresh(order)
        logger.info(f"Created order {order.order_id}")
        return order
    
    @staticmethod
    async def get_by_order_id(session: AsyncSession, order_id: str) -> OrderModel:
        result = await session.execute(select(OrderModel).where(OrderModel.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundError(message=f"Order {order_id} not found")
        return order
    
    @staticmethod
    async def update_status(session: AsyncSession, order_id: str, new_status: str) -> OrderModel:
        order = await OrderRepository.get_by_order_id(session, order_id)
        order.status = new_status
        await session.flush()
        await session.refresh(order)
        logger.info(f"Updated order {order.order_id} status to {new_status}")
        return order


class AuditRepository:
    @staticmethod
    async def log_event(
        session: AsyncSession,
        event_type: str,
        user_id: str | None = None,
        provider_id: str | None = None,
        product_id: str | None = None,
        order_id: str | None = None,
        amount: int | None = None,
        reason: str | None = None,
        result: str | None = None,
        metadata: dict | None = None,
    ) -> AuditEventModel:
        event = AuditEventModel(
            event_type=event_type,
            user_id=user_id,
            provider_id=provider_id,
            product_id=product_id,
            order_id=order_id,
            amount=amount,
            reason=reason,
            result=result,
            metadata_json=metadata,
        )
        session.add(event)
        await session.flush()
        logger.info(f"Logged audit event {event_type}")
        return event
