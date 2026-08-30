from __future__ import annotations

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import DatabaseManager, init_database_manager
from app.domain.enums import (
    AvailabilityStatus,
    FulfillmentType,
    ProductCategory,
    ProviderType,
)
from app.domain.schemas import ProductCreateSchema, ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService
from app.services.vector_service import VectorService, get_vector_service

logger = get_logger(__name__)

SEED_PROVIDERS = [
    {
        "merchant": ProviderCreateSchema(
            name="Sharma Sweets",
            type=ProviderType.LOCAL_MERCHANT,
            description="Authentic traditional Indian sweets & snacks established in 1985.",
            location="Connaught Place, New Delhi",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Rasgulla",
                description="Fresh, soft, spongy cottage cheese balls soaked in chilled aromatic sugar syrup (1 kg).",
                category=ProductCategory.SWEETS,
                price_amount=45000,  # ₹450
                price_currency="INR",
                quantity=50,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=20,
                slot_capacity=10,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Gulab Jamun",
                description="Traditional deep-fried milk solid dumplings soaked in rose-flavored cardamom syrup (1 kg).",
                category=ProductCategory.SWEETS,
                price_amount=40000,  # ₹400
                price_currency="INR",
                quantity=30,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=15,
                slot_capacity=10,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Kaju Katli",
                description="Premium diamond-cut cashew fudge made with pure cashews and edible silver leaf (500g).",
                category=ProductCategory.SWEETS,
                price_amount=80000,  # ₹800
                price_currency="INR",
                quantity=25,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=10,
                slot_capacity=15,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Jalebi",
                description="Crispy, golden, piping hot spiral sweets soaked in saffron sugar syrup (500g).",
                category=ProductCategory.SWEETS,
                price_amount=30000,  # ₹300
                price_currency="INR",
                quantity=100,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=15,
                slot_capacity=20,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Samosa",
                description="Crispy golden pastry filled with spicy spiced potato and green peas (2 pcs).",
                category=ProductCategory.FOOD,
                price_amount=2000,  # ₹20
                price_currency="INR",
                quantity=200,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=5,
                slot_capacity=50,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Sweet Lassi",
                description="Thick, creamy traditional yogurt drink topped with rich malai and saffron (300ml).",
                category=ProductCategory.BEVERAGES,
                price_amount=6000,  # ₹60
                price_currency="INR",
                quantity=50,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=5,
                slot_capacity=30,
                pincode="110001",
            ),
        ],
    },
    {
        "merchant": ProviderCreateSchema(
            name="Blinkit (CP Dark Store)",
            type=ProviderType.ENTERPRISE,
            description="Blinkit quick-commerce fulfillment node serving central Delhi.",
            location="Connaught Place Outer Circle, Delhi",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Haldiram Rasgulla Tin",
                description="Packaged Haldiram's Bengali Rasgulla Tin (1 kg) delivered in 10 minutes.",
                category=ProductCategory.SWEETS,
                price_amount=38000,  # ₹380
                price_currency="INR",
                quantity=40,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=10,
                slot_capacity=100,
                pincode="110001",
            ),
        ],
    },
    {
        "merchant": ProviderCreateSchema(
            name="Zepto (CP Hub)",
            type=ProviderType.ENTERPRISE,
            description="Zepto 10-minute delivery dark store node.",
            location="Barakhamba Road, Delhi",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Bikano Rasgulla Tin",
                description="Bikano Premium Rasgulla Tin (1 kg) with lightning-fast 8-minute delivery.",
                category=ProductCategory.SWEETS,
                price_amount=35000,  # ₹350
                price_currency="INR",
                quantity=35,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=8,
                slot_capacity=100,
                pincode="110001",
            ),
        ],
    },
]


async def seed_database(
    session: AsyncSession,
    vector_service: VectorService | None = None,
) -> None:
    """Seeds the database with initial merchants and products."""
    existing_merchants = await MerchantService.list_merchants(session)
    if existing_merchants:
        logger.info("Database already seeded with merchants. Skipping.")
        return

    logger.info("Seeding database with demo merchants and products...")
    for item in SEED_PROVIDERS:
        merchant_schema = await MerchantService.register_merchant(
            session=session,
            data=item["merchant"],
        )
        logger.info(f"Seeded merchant: {merchant_schema.name} ({merchant_schema.provider_id})")

        for product_data in item["products"]:
            product_schema = await ProductService.add_product(
                session=session,
                merchant_id=merchant_schema.provider_id,
                data=product_data,
                vector_service=vector_service,
            )
            logger.info(f"  -> Seeded product: {product_schema.name} at ₹{product_schema.pricing.amount / 100}")

    logger.info("Database seeding completed successfully.")


async def main() -> None:
    """CLI runner for database seeding."""
    settings = get_settings()
    db_manager = init_database_manager(settings.DATABASE_URL)
    await db_manager.init_db()

    vector_service = get_vector_service()
    await vector_service.ensure_collection()

    async for session in db_manager.get_session():
        await seed_database(session, vector_service)
        break

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
