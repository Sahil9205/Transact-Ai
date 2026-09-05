from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import MerchantModel
from app.db.repository import AuditRepository, MerchantRepository
from app.domain.enums import AuditEventType, ProviderType
from app.domain.schemas import ProviderCreateSchema, ProviderSchema

logger = get_logger(__name__)


def merchant_model_to_schema(merchant: MerchantModel) -> ProviderSchema:
    """Converts MerchantModel ORM instance to canonical ProviderSchema."""
    return ProviderSchema(
        provider_id=merchant.merchant_id,
        name=merchant.name,
        type=ProviderType(merchant.type),
        description=merchant.description,
        location=merchant.location,
        pincode=merchant.pincode,
        is_active=merchant.is_active,
        api_key=getattr(merchant, "api_key", None),
        contact_email=getattr(merchant, "contact_email", None),
        contact_phone=getattr(merchant, "contact_phone", None),
        business_type=getattr(merchant, "business_type", "general"),
        onboarding_status=getattr(merchant, "onboarding_status", "active"),
        operational_status=getattr(merchant, "operational_status", "open"),
        logo_url=getattr(merchant, "logo_url", None),
        payout_upi_id=getattr(merchant, "payout_upi_id", None),
        payout_bank_account=getattr(merchant, "payout_bank_account", None),
        payout_ifsc_code=getattr(merchant, "payout_ifsc_code", None),
    )


class MerchantService:
    """Service for handling business logic related to merchants/providers."""

    @staticmethod
    async def register_merchant(session: AsyncSession, data: ProviderCreateSchema) -> ProviderSchema:
        """Registers a new merchant and logs an audit event."""
        logger.info(f"Registering merchant: {data.name}")
        merchant = await MerchantRepository.create(session, data)

        await AuditRepository.log_event(
            session,
            event_type=AuditEventType.DISCOVERY_STARTED,
            provider_id=merchant.merchant_id,
            reason=f"Merchant '{data.name}' registered",
            result="SUCCESS",
            metadata={
                "contact_email": data.contact_email,
                "contact_phone": data.contact_phone,
                "business_type": data.business_type,
            },
        )

        return merchant_model_to_schema(merchant)

    @staticmethod
    async def get_merchant(session: AsyncSession, merchant_id: str) -> ProviderSchema:
        """Retrieves a merchant by ID."""
        logger.debug(f"Retrieving merchant: {merchant_id}")
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
        return merchant_model_to_schema(merchant)

    @staticmethod
    async def get_merchant_by_api_key(session: AsyncSession, api_key: str) -> ProviderSchema | None:
        """Retrieves a merchant by their API key."""
        merchant = await MerchantRepository.get_by_api_key(session, api_key)
        return merchant_model_to_schema(merchant) if merchant else None

    @staticmethod
    async def update_merchant(session: AsyncSession, merchant_id: str, data: dict) -> ProviderSchema:
        """Updates merchant profile fields."""
        merchant = await MerchantRepository.update(session, merchant_id, data)
        return merchant_model_to_schema(merchant)

    @staticmethod
    async def list_merchants(session: AsyncSession) -> list[ProviderSchema]:
        """Lists active merchants."""
        logger.debug("Listing active merchants")
        merchants = await MerchantRepository.list_active(session)
        return [merchant_model_to_schema(m) for m in merchants]

    @staticmethod
    async def get_dashboard_stats(session: AsyncSession, merchant_id: str) -> dict:
        """Computes summary metrics and recent orders for merchant portal."""
        from sqlalchemy import select, func
        from app.db.models import ProductModel, OrderModel
        
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
        
        # Product count
        prod_count_stmt = select(func.count(ProductModel.id)).where(ProductModel.merchant_id == merchant_id)
        res_p = await session.execute(prod_count_stmt)
        total_products = res_p.scalar() or 0
        
        # Orders and revenue
        orders_stmt = select(OrderModel).where(OrderModel.merchant_id == merchant_id).order_by(OrderModel.created_at.desc())
        res_o = await session.execute(orders_stmt)
        all_orders = list(res_o.scalars().all())
        
        total_orders = len(all_orders)
        total_revenue_paise = sum(
            o.total_amount for o in all_orders 
            if o.status in ["payment_success", "completed", "ready_for_pickup", "order_created"]
        )
        
        # Platform breakdown
        platforms = {}
        # Products list for catalog table
        products_stmt = select(ProductModel).where(ProductModel.merchant_id == merchant_id).order_by(ProductModel.created_at.desc())
        res_prods = await session.execute(products_stmt)
        products = list(res_prods.scalars().all())
        products_data = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "price_amount": p.price_amount,
                "price_currency": p.price_currency,
                "price_inr": round(p.price_amount / 100, 2),
                "pricing_type": getattr(p, "pricing_type", "fixed_unit"),
                "unit": getattr(p, "unit", "piece"),
                "min_quantity": getattr(p, "min_quantity", 1.0),
                "increment_step": getattr(p, "increment_step", 1.0),
                "quantity": p.quantity,
                "availability_status": p.availability_status,
                "fulfillment_type": p.fulfillment_type,
                "prep_time_minutes": p.prep_time_minutes,
                "pincode": p.pincode,
            }
            for p in products
        ]
            
        return {
            "merchant": merchant_model_to_schema(merchant),
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue_inr": round(total_revenue_paise / 100, 2),
            "platform_breakdown": platforms,
            "recent_orders": all_orders[:25],
            "products": products_data,
        }

    @staticmethod
    async def set_operational_status(session: AsyncSession, merchant_id: str, status: str) -> ProviderSchema:
        """Sets the store's operational status (open, paused, closed)."""
        merchant = await MerchantRepository.update(session, merchant_id, {"operational_status": status})
        return merchant_model_to_schema(merchant)

    @staticmethod
    async def set_product_availability(session: AsyncSession, product_id: str, status: str) -> dict:
        """Sets product availability status (in_stock, out_of_stock, limited)."""
        from app.db.repository import ProductRepository
        from app.domain.schemas import ProductUpdateSchema
        from app.domain.enums import AvailabilityStatus
        product = await ProductRepository.update(
            session, product_id, ProductUpdateSchema(availability_status=AvailabilityStatus(status))
        )
        return {
            "product_id": product.product_id,
            "availability_status": product.availability_status,
            "quantity": product.quantity,
        }
