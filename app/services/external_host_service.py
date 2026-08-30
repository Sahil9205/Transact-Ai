from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.domain.schemas import BuyerIntentSchema
from app.services.audit_service import AuditService
from app.services.discovery_service import DiscoveryService
from app.services.gatekeeper_service import GatekeeperService
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService
from app.services.recovery_service import RecoveryService

logger = get_logger(__name__)

CANONICAL_COMMERCE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_products",
        "description": "Searches for products matching a buyer prompt with semantic Qdrant matching and multi-factor ranking.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query like 'Rasgulla', 'Kaju Katli', 'Milk'"},
                "max_price_inr": {"type": "number", "description": "Optional maximum budget ceiling in INR"},
                "pincode": {"type": "string", "description": "Delivery destination pincode (e.g. '110001')"},
                "limit": {"type": "integer", "description": "Maximum number of candidate items to return (default: 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_product_details",
        "description": "Fetches live price, stock quantity, freshness tier, and merchant details for a specific product ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Unique UUID of the product"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "verify_order_preflight",
        "description": "Performs authoritative live DB stock, price freshness, and user daily spending policy checks before placing an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "ID of buyer placing the order"},
                "product_id": {"type": "string", "description": "Product UUID to verify"},
                "quantity": {"type": "integer", "description": "Number of units to purchase (default: 1)"},
            },
            "required": ["user_id", "product_id"],
        },
    },
    {
        "name": "create_payment_order",
        "description": "Initializes a test-mode Razorpay checkout order and generates an instant payment link for a confirmed item.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Buyer user ID"},
                "product_id": {"type": "string", "description": "Product UUID"},
                "quantity": {"type": "integer", "description": "Quantity to buy (default: 1)"},
            },
            "required": ["user_id", "product_id"],
        },
    },
    {
        "name": "get_order_timeline",
        "description": "Retrieves the immutable 3-layer audit trail and chronological history for an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Internal Order UUID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "find_smart_alternatives",
        "description": "Finds verified alternative in-stock products across 4 relaxation dimensions (Price Headroom, Timeline Extension, Cross-Platform Switching, and Category Substitutes).",
        "parameters": {
            "type": "object",
            "properties": {
                "product_query": {"type": "string", "description": "Product query that had no match or went out of stock"},
                "max_price_inr": {"type": "number", "description": "Original budget ceiling"},
                "pincode": {"type": "string", "description": "Delivery destination pincode"},
                "limit": {"type": "integer", "description": "Max suggestions to return (default: 3)"},
            },
            "required": ["product_query"],
        },
    },
]


class ExternalHostService:
    """External AI Host Connector and Universal Tool Dispatcher."""

    @staticmethod
    def get_host_tools_schema(format: str = "openai") -> list[dict[str, Any]]:
        """Converts canonical commerce tools into host-native function definitions."""
        fmt = format.lower().strip()

        if fmt == "gemini":
            # Google Gemini format
            return [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                }
                for t in CANONICAL_COMMERCE_TOOLS
            ]
        elif fmt == "anthropic":
            # Anthropic Claude tool use format
            return [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["parameters"],
                }
                for t in CANONICAL_COMMERCE_TOOLS
            ]
        else:
            # OpenAI ChatGPT / standard tool calling format
            return [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    },
                }
                for t in CANONICAL_COMMERCE_TOOLS
            ]

    @staticmethod
    async def dispatch_tool_call(
        session: AsyncSession,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        """Universal dispatcher executing external AI tool calls against Transact AI core."""
        logger.info("Executing external AI tool call", tool=tool_name, args=arguments, user_id=user_id)

        try:
            if tool_name == "search_products":
                query = arguments.get("query", "")
                max_price = int(arguments["max_price_inr"] * 100) if "max_price_inr" in arguments and arguments["max_price_inr"] is not None else None
                pincode = arguments.get("pincode")
                limit = arguments.get("limit", 5)

                intent = BuyerIntentSchema(product_query=query, max_price=max_price, pincode=pincode)
                candidates = await DiscoveryService.match_candidates(session, intent)
                if limit and len(candidates) > limit:
                    candidates = candidates[:limit]
                return {
                    "tool": tool_name,
                    "success": True,
                    "total_matches": len(candidates),
                    "candidates": [c.model_dump(mode="json") for c in candidates],
                }

            elif tool_name == "get_product_details":
                product_id = arguments.get("product_id", "")
                product = await ProductService.get_product(session, product_id)
                return {
                    "tool": tool_name,
                    "success": True,
                    "product": product.model_dump(mode="json"),
                }

            elif tool_name == "verify_order_preflight":
                u_id = arguments.get("user_id", user_id)
                product_id = arguments.get("product_id", "")
                quantity = arguments.get("quantity", 1)

                decision = await GatekeeperService.verify_and_authorize(
                    session=session,
                    user_id=u_id,
                    product_id=product_id,
                    quantity=quantity,
                )
                return {
                    "tool": tool_name,
                    "success": decision.is_authorized,
                    "gatekeeper_decision": decision.model_dump(mode="json"),
                }

            elif tool_name == "create_payment_order":
                u_id = arguments.get("user_id", user_id)
                product_id = arguments.get("product_id", "")
                quantity = arguments.get("quantity", 1)

                order_res = await PaymentService.create_payment_order(
                    session=session,
                    user_id=u_id,
                    product_id=product_id,
                    quantity=quantity,
                )
                return {
                    "tool": tool_name,
                    "success": True,
                    "payment_order": order_res.model_dump(mode="json"),
                }

            elif tool_name == "get_order_timeline":
                order_id = arguments.get("order_id", "")
                timeline = await AuditService.get_order_timeline(session, order_id)
                return {
                    "tool": tool_name,
                    "success": True,
                    "order_timeline": timeline.model_dump(mode="json"),
                }

            elif tool_name == "find_smart_alternatives":
                query = arguments.get("product_query", "")
                max_price = int(arguments["max_price_inr"] * 100) if "max_price_inr" in arguments and arguments["max_price_inr"] is not None else None
                pincode = arguments.get("pincode")
                limit = arguments.get("limit", 3)

                intent = BuyerIntentSchema(product_query=query, max_price=max_price, pincode=pincode)
                alts = await RecoveryService.find_smart_alternatives(session, intent, limit=limit)
                return {
                    "tool": tool_name,
                    "success": True,
                    "alternatives": [a.model_dump(mode="json") for a in alts],
                }

            else:
                return {
                    "tool": tool_name,
                    "success": False,
                    "error": f"Unknown tool '{tool_name}'",
                }

        except Exception as e:
            logger.error("Tool execution error", tool=tool_name, error=str(e))
            return {
                "tool": tool_name,
                "success": False,
                "error": str(e),
            }
