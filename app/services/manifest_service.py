from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import MerchantModel, ProductModel
from app.db.repository import MerchantRepository, ProductRepository
from app.domain.enums import FreshnessTier, ProviderType
from app.domain.manifest_schemas import (
    AgentToolDescriptorSchema,
    CapabilitySchema,
    CategorySummarySchema,
    ConnectedMerchantSummary,
    GlobalDirectoryManifestSchema,
    MerchantManifestSchema,
    PolicySummarySchema,
)
from app.services.product_service import compute_freshness_tier

logger = get_logger(__name__)


class ManifestService:
    """Service for compiling dynamic, agent-readable manifests for merchants and the global network."""

    @staticmethod
    async def generate_merchant_manifest(
        session: AsyncSession,
        merchant_id: str,
    ) -> MerchantManifestSchema:
        """Dynamically synthesizes the agent-readable manifest for a specific merchant."""
        logger.debug(f"Generating manifest for merchant: {merchant_id}")
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
        products = await ProductRepository.search(session, merchant_id=merchant_id)

        # 1. Category Breakdown
        categories_map: dict[str, list[ProductModel]] = {}
        for p in products:
            cat = p.category
            if cat not in categories_map:
                categories_map[cat] = []
            categories_map[cat].append(p)

        category_summaries: list[CategorySummarySchema] = []
        for cat_name, cat_prods in categories_map.items():
            prices = [p.price_amount for p in cat_prods]
            category_summaries.append(
                CategorySummarySchema(
                    category=cat_name,
                    product_count=len(cat_prods),
                    min_price_amount=min(prices) if prices else 0,
                    max_price_amount=max(prices) if prices else 0,
                    currency=cat_prods[0].price_currency if cat_prods else "INR",
                )
            )

        # 2. Capabilities & SLAs
        can_pickup = any(p.fulfillment_type in ("pickup", "both") for p in products) if products else True
        can_deliver = any(p.fulfillment_type in ("delivery", "both") for p in products) if products else False
        pincodes = list({p.pincode for p in products if p.pincode})
        if merchant.pincode and merchant.pincode not in pincodes:
            pincodes.append(merchant.pincode)

        prep_times = [p.prep_time_minutes for p in products if p.prep_time_minutes > 0]
        avg_prep_time = int(sum(prep_times) / len(prep_times)) if prep_times else 15
        slot_caps = [p.slot_capacity for p in products if p.slot_capacity is not None]
        max_slot_cap = max(slot_caps) if slot_caps else None

        capabilities = CapabilitySchema(
            can_pickup=can_pickup,
            can_deliver=can_deliver,
            delivery_pincodes=pincodes,
            avg_prep_time_minutes=avg_prep_time,
            slot_capacity=max_slot_cap,
        )

        # 3. Standard Policies
        policies = PolicySummarySchema(
            cancellation_allowed=True,
            cancellation_window_minutes=5 if can_deliver else 10,
            return_policy="Full refund if canceled before fulfillment. No returns on perishable items after dispatch.",
            accepted_currencies=["INR"],
            payment_methods=["razorpay_upi", "razorpay_card", "razorpay_netbanking"],
        )

        # 4. Actionable Tools for AI Agents
        available_tools = [
            AgentToolDescriptorSchema(
                name="search_merchant_products",
                description=f"Search available products, sweets, and snacks in {merchant.name}'s live catalog.",
                endpoint_url="/api/v1/products/search",
                http_method="GET",
                parameters={
                    "type": "object",
                    "properties": {
                        "q": {"type": "string", "description": "Keyword search query (e.g. 'rasgulla', 'samosa')"},
                        "category": {"type": "string", "description": "Filter by category (e.g. 'sweets', 'food')"},
                        "merchant_id": {"type": "string", "default": merchant.merchant_id},
                    },
                },
            ),
            AgentToolDescriptorSchema(
                name="get_product_details",
                description="Fetch real-time price, stock quantity, and fulfillment time for a specific product ID.",
                endpoint_url="/api/v1/products/{product_id}",
                http_method="GET",
                parameters={
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "Unique product UUID"},
                    },
                    "required": ["product_id"],
                },
            ),
        ]

        # 5. Determine Freshness
        latest_verified = max((p.last_verified for p in products), default=datetime.now(timezone.utc))
        freshness = compute_freshness_tier(latest_verified)

        return MerchantManifestSchema(
            manifest_version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            freshness_tier=freshness,
            provider_id=merchant.merchant_id,
            name=merchant.name,
            type=ProviderType(merchant.type),
            description=merchant.description,
            location=merchant.location,
            pincode=merchant.pincode,
            capabilities=capabilities,
            policies=policies,
            categories=category_summaries,
            total_active_products=len(products),
            available_tools=available_tools,
        )

    @staticmethod
    async def generate_global_manifest(
        session: AsyncSession,
    ) -> GlobalDirectoryManifestSchema:
        """Compiles system-wide manifest indexing all registered commerce providers."""
        logger.debug("Generating global directory manifest")
        merchants = await MerchantRepository.list_active(session)

        merchant_summaries: list[ConnectedMerchantSummary] = []
        all_pincodes_set: set[str] = set()
        all_categories_set: set[str] = set()
        total_products_count = 0

        for m in merchants:
            prods = await ProductRepository.search(session, merchant_id=m.merchant_id)
            total_products_count += len(prods)
            cats = list({p.category for p in prods})
            all_categories_set.update(cats)
            
            pincs = {p.pincode for p in prods if p.pincode}
            if m.pincode:
                pincs.add(m.pincode)
            all_pincodes_set.update(pincs)

            merchant_summaries.append(
                ConnectedMerchantSummary(
                    provider_id=m.merchant_id,
                    name=m.name,
                    type=ProviderType(m.type),
                    location=m.location,
                    pincode=m.pincode,
                    category_names=cats,
                    product_count=len(prods),
                    manifest_url=f"/api/v1/merchants/{m.merchant_id}/manifest.json",
                )
            )

        return GlobalDirectoryManifestSchema(
            manifest_version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            total_merchants=len(merchants),
            total_products=total_products_count,
            supported_pincodes=sorted(list(all_pincodes_set)),
            all_categories=sorted(list(all_categories_set)),
            merchants=merchant_summaries,
        )

    @staticmethod
    async def generate_schema_org_jsonld(
        session: AsyncSession,
        merchant_id: str,
    ) -> dict[str, Any]:
        """Generates standard schema.org/Store JSON-LD for semantic web/agent discovery."""
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
        products = await ProductRepository.search(session, merchant_id=merchant_id)

        offers = []
        for p in products:
            offers.append(
                {
                    "@type": "Offer",
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                    "price": f"{p.price_amount / 100:.2f}",
                    "priceCurrency": p.price_currency,
                    "availability": (
                        "https://schema.org/InStock"
                        if p.availability_status == "in_stock"
                        else "https://schema.org/OutOfStock"
                    ),
                    "itemOffered": {
                        "@type": "Product",
                        "productID": p.product_id,
                        "name": p.name,
                        "description": p.description,
                    },
                }
            )

        return {
            "@context": "https://schema.org",
            "@type": "Store",
            "identifier": merchant.merchant_id,
            "name": merchant.name,
            "description": merchant.description,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": merchant.location or "",
                "postalCode": merchant.pincode or "",
                "addressCountry": "IN",
            },
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": f"{merchant.name} Catalog",
                "itemListElement": offers,
            },
        }
