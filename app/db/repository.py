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
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            business_type=data.business_type or "general",
            logo_url=data.logo_url,
            onboarding_status="active",
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
    async def get_by_merchant_ids(session: AsyncSession, merchant_ids: list[str]) -> dict[str, MerchantModel]:
        """Batch fetches merchants by IDs in a single SQL query, returning a lookup dict {merchant_id: MerchantModel}."""
        if not merchant_ids:
            return {}
        result = await session.execute(
            select(MerchantModel).where(MerchantModel.merchant_id.in_(merchant_ids))
        )
        merchants = result.scalars().all()
        return {m.merchant_id: m for m in merchants}
    
    @staticmethod
    async def get_by_api_key(session: AsyncSession, api_key: str) -> MerchantModel | None:
        result = await session.execute(select(MerchantModel).where(MerchantModel.api_key == api_key))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_active(session: AsyncSession) -> list[MerchantModel]:
        result = await session.execute(select(MerchantModel).where(MerchantModel.is_active == True))
        return list(result.scalars().all())

    @staticmethod
    async def resolve_pincode_from_db(session: AsyncSession, text: str) -> str | None:
        """Dynamically resolves a postal pincode by querying active merchants from the database.
        Checks merchant location and name fields against text keywords (Zero hardcoding)."""
        if not text or not text.strip():
            return None
        import re
        result = await session.execute(
            select(MerchantModel.pincode, MerchantModel.location, MerchantModel.name)
            .where(MerchantModel.is_active == True)
        )
        merchants = result.all()
        text_lower = text.lower()
        for pin, loc, name in merchants:
            if not pin:
                continue
            # Match location segments (e.g. "Karol Bagh", "Connaught Place", "Chandni Chowk", "Indiranagar")
            if loc:
                segments = [seg.strip().lower() for seg in loc.split(",") if seg.strip()]
                for seg in segments:
                    if len(seg) >= 3:
                        if re.search(rf"\b{re.escape(seg)}\b", text_lower):
                            return pin
                        base_seg = re.sub(r"\b(i+|iv|v|vi*|part\s*\d+|block\s*\w+|phase\s*\d+)\b", "", seg).strip()
                        if len(base_seg) >= 3 and re.search(rf"\b{re.escape(base_seg)}\b", text_lower):
                            return pin
            # Match merchant name (e.g. "Roshan Di Kulfi", "Sharma Sweets")
            if name and len(name) >= 3:
                if re.search(rf"\b{re.escape(name.lower())}\b", text_lower):
                    return pin
        return None

    @staticmethod
    async def update(session: AsyncSession, merchant_id: str, update_dict: dict) -> MerchantModel:
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
        for key, value in update_dict.items():
            if value is not None and hasattr(merchant, key):
                setattr(merchant, key, value)
        await session.flush()
        await session.refresh(merchant)
        logger.info(f"Updated merchant {merchant.merchant_id}")
        return merchant


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
            pricing_type=data.pricing_type.value if hasattr(data.pricing_type, "value") else str(data.pricing_type),
            unit=data.unit,
            min_quantity=data.min_quantity,
            increment_step=data.increment_step,
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
    async def get_by_product_ids(session: AsyncSession, product_ids: list[str]) -> list[ProductModel]:
        """Batch fetches products by IDs in a single SQL query."""
        if not product_ids:
            return []
        result = await session.execute(
            select(ProductModel).where(ProductModel.product_id.in_(product_ids))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def search(
        session: AsyncSession,
        query: str | None = None,
        category: str | None = None,
        pincode: str | None = None,
        merchant_id: str | None = None,
    ) -> list[ProductModel]:
        from sqlalchemy import or_
        stmt = (
            select(ProductModel)
            .join(MerchantModel, ProductModel.merchant_id == MerchantModel.merchant_id, isouter=True)
        )
        if category:
            stmt = stmt.where(ProductModel.category == category)
        if pincode:
            stmt = stmt.where(ProductModel.pincode == pincode)
        if merchant_id:
            stmt = stmt.where(ProductModel.merchant_id == merchant_id)
        if query:
            words = [w.strip() for w in query.split() if len(w.strip()) > 2]
            if words:
                conditions = []
                for w in words:
                    conditions.append(ProductModel.name.ilike(f"%{w}%"))
                    conditions.append(ProductModel.description.ilike(f"%{w}%"))
                    conditions.append(MerchantModel.name.ilike(f"%{w}%"))
                    conditions.append(MerchantModel.location.ilike(f"%{w}%"))
                stmt = stmt.where(or_(*conditions))
            else:
                stmt = stmt.where(
                    or_(
                        ProductModel.name.ilike(f"%{query}%"),
                        MerchantModel.name.ilike(f"%{query}%"),
                        MerchantModel.location.ilike(f"%{query}%"),
                    )
                )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def update(session: AsyncSession, product_id: str, data: ProductUpdateSchema) -> ProductModel:
        product = await ProductRepository.get_by_product_id(session, product_id)
        update_data = data.model_dump(exclude_unset=True)
        # Convert enum values to strings
        if 'availability_status' in update_data and update_data['availability_status'] is not None:
            update_data['availability_status'] = update_data['availability_status'].value if hasattr(update_data['availability_status'], 'value') else update_data['availability_status']
        if 'pricing_type' in update_data and update_data['pricing_type'] is not None:
            update_data['pricing_type'] = update_data['pricing_type'].value if hasattr(update_data['pricing_type'], 'value') else update_data['pricing_type']
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
        currency: str = "INR",
        pincode: str | None = None,
        delivery_address: str | None = None,
        platform: str | None = None,
    ) -> OrderModel:
        order = OrderModel(
            user_id=user_id,
            merchant_id=merchant_id,
            product_id=product_id,
            quantity=quantity,
            total_amount=total_amount,
            currency=currency,
            pincode=pincode,
            delivery_address=delivery_address,
            platform=platform or "api",
        )
        session.add(order)
        await session.flush()
        await session.refresh(order)
        logger.info(f"Created order {order.order_id} via {order.platform}")
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
