from __future__ import annotations

import json
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.enums import ProductCategory
from app.domain.schemas import ProductSchema
from app.services.manifest_service import ManifestService
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService

logger = get_logger(__name__)

# Standard MCP Tool Definitions conforming to Model Context Protocol schema
MCP_TOOLS_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "transact_discover_merchants",
        "description": "Discover active merchants and commerce providers in the Transact AI network filtered by location or category.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pincode": {
                    "type": "string",
                    "description": "6-digit delivery pincode (e.g. '110001')",
                },
                "category": {
                    "type": "string",
                    "description": "Product category filter (e.g. 'sweets', 'food', 'groceries', 'beverages')",
                },
            },
        },
    },
    {
        "name": "transact_search_catalog",
        "description": "Search products across all connected providers (Sharma Sweets, Blinkit, Zepto) with budget and location constraints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term or item name (e.g. 'rasgulla', 'gulab jamun', 'samosa')",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter ('sweets', 'food', 'groceries', 'beverages')",
                },
                "max_price_inr": {
                    "type": "number",
                    "description": "Maximum budget ceiling in Indian Rupees (e.g. 500 for ₹500)",
                },
                "pincode": {
                    "type": "string",
                    "description": "Optional 6-digit delivery pincode (e.g. '110001')",
                },
                "merchant_id": {
                    "type": "string",
                    "description": "Optional merchant UUID to restrict search to a single shop",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "transact_get_product",
        "description": "Get authoritative real-time details, pricing, fulfillment SLA, and data freshness tier for a specific product.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Unique product UUID",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "transact_check_availability",
        "description": "Check live inventory stock and fulfillment readiness before proposing an order to the user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Unique product UUID",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "transact_get_merchant_manifest",
        "description": "Retrieve the complete agent-readable manifest for a merchant including SLAs, price spans, and refund policies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "merchant_id": {
                    "type": "string",
                    "description": "Unique merchant provider UUID",
                },
            },
            "required": ["merchant_id"],
        },
    },
    {
        "name": "transact_create_order_payment",
        "description": "Place a purchase order and generate an instant Razorpay checkout payment link for a confirmed product.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Unique UUID of the product to purchase",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of units to buy (default: 1)",
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional buyer user ID (default: 'buyer_default')",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "transact_verify_order_preflight",
        "description": "Performs authoritative live DB stock, price freshness, and user daily spending policy checks before placing an order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product UUID to verify",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of units to purchase (default: 1)",
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional buyer user ID",
                },
            },
            "required": ["product_id"],
        },
    },
]


class MCPCommerceTools:
    """Executes commerce actions requested by external AI agents via MCP."""

    @staticmethod
    async def discover_merchants(
        session: AsyncSession,
        pincode: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Tool handler for transact_discover_merchants."""
        global_manifest = await ManifestService.generate_global_manifest(session)
        merchants = global_manifest.merchants

        if pincode:
            merchants = [m for m in merchants if m.pincode == pincode or not m.pincode]
        if category:
            merchants = [m for m in merchants if category.lower() in [c.lower() for c in m.category_names]]

        return {
            "total_found": len(merchants),
            "merchants": [
                {
                    "provider_id": m.provider_id,
                    "name": m.name,
                    "type": m.type.value,
                    "location": m.location,
                    "pincode": m.pincode,
                    "categories": m.category_names,
                    "product_count": m.product_count,
                    "manifest_url": m.manifest_url,
                }
                for m in merchants
            ],
        }

    @staticmethod
    async def search_catalog(
        session: AsyncSession,
        query: str,
        category: str | None = None,
        max_price_inr: float | None = None,
        pincode: str | None = None,
        merchant_id: str | None = None,
    ) -> dict[str, Any]:
        """Tool handler for transact_search_catalog."""
        products = await ProductService.search_products(
            session=session,
            query=query,
            category=category,
            pincode=pincode,
            merchant_id=merchant_id,
        )

        # Convert max_price_inr to paise if provided
        max_paise = int(max_price_inr * 100) if max_price_inr is not None else None
        if max_paise is not None:
            products = [p for p in products if p.pricing.amount <= max_paise]

        return {
            "query": query,
            "total_matches": len(products),
            "products": [
                {
                    "product_id": p.product_id,
                    "provider_id": p.provider_id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category.value,
                    "price_inr": p.pricing.amount / 100,
                    "price_amount_paise": p.pricing.amount,
                    "currency": p.pricing.currency,
                    "availability": p.availability.status.value,
                    "stock_quantity": p.availability.quantity,
                    "fulfillment_type": p.fulfillment.type.value,
                    "prep_time_minutes": p.fulfillment.prep_time_minutes,
                    "pincode": p.pincode,
                    "freshness_tier": p.verification.freshness_tier.value,
                }
                for p in products
            ],
        }

    @staticmethod
    async def get_product(
        session: AsyncSession,
        product_id: str,
    ) -> dict[str, Any]:
        """Tool handler for transact_get_product."""
        product = await ProductService.get_product(session, product_id)
        return {
            "product_id": product.product_id,
            "provider_id": product.provider_id,
            "name": product.name,
            "description": product.description,
            "category": product.category.value,
            "price_inr": product.pricing.amount / 100,
            "price_amount_paise": product.pricing.amount,
            "currency": product.pricing.currency,
            "availability": product.availability.status.value,
            "stock_quantity": product.availability.quantity,
            "fulfillment_type": product.fulfillment.type.value,
            "prep_time_minutes": product.fulfillment.prep_time_minutes,
            "pincode": product.pincode,
            "freshness_tier": product.verification.freshness_tier.value,
            "last_verified": product.verification.last_verified.isoformat(),
        }

    @staticmethod
    async def check_availability(
        session: AsyncSession,
        product_id: str,
    ) -> dict[str, Any]:
        """Tool handler for transact_check_availability."""
        product = await ProductService.get_product(session, product_id)
        is_available = product.availability.status.value == "in_stock" and (
            product.availability.quantity is None or product.availability.quantity > 0
        )
        return {
            "product_id": product.product_id,
            "name": product.name,
            "is_available": is_available,
            "status": product.availability.status.value,
            "available_quantity": product.availability.quantity,
            "prep_time_minutes": product.fulfillment.prep_time_minutes,
            "fulfillment_type": product.fulfillment.type.value,
            "freshness_tier": product.verification.freshness_tier.value,
        }

    @staticmethod
    async def get_merchant_manifest(
        session: AsyncSession,
        merchant_id: str,
    ) -> dict[str, Any]:
        """Tool handler for transact_get_merchant_manifest."""
        manifest = await ManifestService.generate_merchant_manifest(session, merchant_id)
        return manifest.model_dump(mode="json")

    @staticmethod
    async def create_order_payment(
        session: AsyncSession,
        product_id: str,
        quantity: int = 1,
        user_id: str = "buyer_default",
    ) -> dict[str, Any]:
        """Tool handler for transact_create_order_payment."""
        from app.services.payment_service import PaymentService
        res = await PaymentService.create_payment_order(
            session=session,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        return {
            "order_id": res.order_id,
            "razorpay_order_id": res.razorpay_order_id,
            "product_id": res.product_id,
            "product_name": res.product_name,
            "quantity": res.quantity,
            "amount_inr": res.amount_inr,
            "amount_paise": res.amount_paise,
            "currency": res.currency,
            "status": res.status,
            "payment_link_url": res.payment_link_url,
            "message": f"Order created successfully for {res.product_name}. Pay ₹{res.amount_inr} using the Razorpay payment link to confirm delivery.",
        }

    @staticmethod
    async def verify_order_preflight(
        session: AsyncSession,
        product_id: str,
        quantity: int = 1,
        user_id: str = "buyer_default",
    ) -> dict[str, Any]:
        """Tool handler for transact_verify_order_preflight."""
        from app.services.gatekeeper_service import GatekeeperService
        decision = await GatekeeperService.verify_and_authorize(
            session=session,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        return decision.model_dump(mode="json")
