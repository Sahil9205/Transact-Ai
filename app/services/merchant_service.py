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
        )

        return merchant_model_to_schema(merchant)

    @staticmethod
    async def get_merchant(session: AsyncSession, merchant_id: str) -> ProviderSchema:
        """Retrieves a merchant by ID."""
        logger.debug(f"Retrieving merchant: {merchant_id}")
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
        return merchant_model_to_schema(merchant)

    @staticmethod
    async def list_merchants(session: AsyncSession) -> list[ProviderSchema]:
        """Lists active merchants."""
        logger.debug("Listing active merchants")
        merchants = await MerchantRepository.list_active(session)
        return [merchant_model_to_schema(m) for m in merchants]
