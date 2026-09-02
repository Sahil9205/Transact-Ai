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
                name="Traditional Rasgulla",
                description="Fresh, soft, spongy cottage cheese balls soaked in chilled aromatic sugar syrup (1 kg).",
                category=ProductCategory.SWEETS,
                price_amount=45000,  # ₹450
                price_currency="INR",
                quantity=50,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=15,
                slot_capacity=10,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Traditional Gulab Jamun",
                description="Traditional deep-fried milk solid dumplings soaked in rose-flavored cardamom syrup (1 kg).",
                category=ProductCategory.SWEETS,
                price_amount=25000,  # ₹250
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
                name="Fresh Samosa",
                description="Crispy golden pastry filled with spicy potato and green peas (2 pcs).",
                category=ProductCategory.FOOD,
                price_amount=4000,  # ₹40
                price_currency="INR",
                quantity=100,
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
            description="Blinkit 10-minute quick-commerce fulfillment node serving central Delhi.",
            location="Connaught Place Outer Circle, Delhi",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Nescafe Classic Instant Coffee Powder (100g Jar)",
                description="100% pure instant coffee powder offering rich aroma and bold coffee flavor.",
                category=ProductCategory.GROCERIES,
                price_amount=29000,  # ₹290
                price_currency="INR",
                quantity=50,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=10,
                slot_capacity=100,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Amul Taaza Homogenised Toned Milk (1 Litre)",
                description="Fresh pasteurised toned milk rich in calcium and protein.",
                category=ProductCategory.GROCERIES,
                price_amount=5400,  # ₹54
                price_currency="INR",
                quantity=60,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=10,
                slot_capacity=100,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Haldiram Bengali Rasgulla Tin (1 kg)",
                description="Packaged Haldiram's traditional soft sponge Rasgulla Tin delivered in 10 minutes.",
                category=ProductCategory.SWEETS,
                price_amount=34000,  # ₹340
                price_currency="INR",
                quantity=40,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=10,
                slot_capacity=100,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Aashirvaad Superior MP Whole Wheat Atta (1 kg)",
                description="Premium 100% pure whole wheat chakki atta flour, freshly milled for soft rotis.",
                category=ProductCategory.GROCERIES,
                price_amount=6500,  # ₹65
                price_currency="INR",
                quantity=50,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=10,
                slot_capacity=100,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Fortune Sunlite Refined Sunflower Oil (1 Litre)",
                description="Refined cooking sunflower oil with essential fatty acids.",
                category=ProductCategory.GROCERIES,
                price_amount=14500,  # ₹145
                price_currency="INR",
                quantity=30,
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
            description="Zepto 8-minute delivery quick-commerce dark store node.",
            location="Barakhamba Road, Delhi",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Bikano Rasgulla Tin (1 kg)",
                description="Bikano Premium Rasgulla Tin with lightning-fast 8-minute delivery.",
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
            ProductCreateSchema(
                name="Nescafe Gold Premium Freeze-Dried Coffee (50g Glass Jar)",
                description="Crafted with Arabica beans for a smoother, richer taste experience.",
                category=ProductCategory.GROCERIES,
                price_amount=39000,  # ₹390
                price_currency="INR",
                quantity=20,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=8,
                slot_capacity=100,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Chilled Classic Cold Coffee Can (250ml)",
                description="Ready-to-drink chilled creamy cold coffee beverage.",
                category=ProductCategory.BEVERAGES,
                price_amount=6000,  # ₹60
                price_currency="INR",
                quantity=40,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=8,
                slot_capacity=100,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Aashirvaad Shudh Chakki Whole Wheat Atta Flour (1 kg)",
                description="Natural stone-ground whole wheat chakki atta flour with 8-minute delivery.",
                category=ProductCategory.GROCERIES,
                price_amount=6200,  # ₹62
                price_currency="INR",
                quantity=45,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=8,
                slot_capacity=100,
                pincode="110001",
            ),
        ],
    },
    {
        "merchant": ProviderCreateSchema(
            name="Amazon India",
            type=ProviderType.MARKETPLACE,
            description="E-commerce marketplace hub offering comprehensive pantry & appliances.",
            location="New Delhi Fulfillment Center",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Nescafe Classic Instant Coffee Jar (200g)",
                description="Economy 200g glass jar of 100% pure instant coffee.",
                category=ProductCategory.GROCERIES,
                price_amount=58000,  # ₹580
                price_currency="INR",
                quantity=100,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=1440,  # 1 day
                slot_capacity=500,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Handheld Electric Milk Frother for Cold Coffee",
                description="Battery operated stainless steel whisk frother for café style cold coffee.",
                category=ProductCategory.GENERAL,
                price_amount=29900,  # ₹299
                price_currency="INR",
                quantity=50,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.DELIVERY,
                prep_time_minutes=1440,
                slot_capacity=500,
                pincode="110001",
            ),
        ],
    },
    {
        "merchant": ProviderCreateSchema(
            name="Apollo Pharmacy",
            type=ProviderType.LOCAL_MERCHANT,
            description="24x7 verified retail pharmacy and healthcare supply.",
            location="Janpath, New Delhi",
            pincode="110001",
        ),
        "products": [
            ProductCreateSchema(
                name="Crocin Advance 650mg (Strip of 15 Tablets)",
                description="Fast pain and fever relief paracetamol tablets.",
                category=ProductCategory.GENERAL,
                price_amount=3000,  # ₹30
                price_currency="INR",
                quantity=150,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=10,
                slot_capacity=50,
                pincode="110001",
            ),
            ProductCreateSchema(
                name="Electral ORS Powder (21.8g Sachet)",
                description="WHO based oral rehydration salt for instant energy and hydration.",
                category=ProductCategory.GENERAL,
                price_amount=2200,  # ₹22
                price_currency="INR",
                quantity=200,
                availability_status=AvailabilityStatus.IN_STOCK,
                fulfillment_type=FulfillmentType.PICKUP,
                prep_time_minutes=5,
                slot_capacity=50,
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

    await session.commit()
    logger.info("Database seeding completed and committed successfully.")


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
