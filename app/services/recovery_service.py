from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import MerchantModel, ProductModel
from app.db.repository import ProductRepository
from app.domain.enums import AvailabilityStatus, ProductCategory
from app.domain.schemas import BuyerIntentSchema, ProductSchema
from app.services.product_service import model_to_schema
from app.services.vector_service import VectorService

logger = get_logger(__name__)


class AlternativeOptionSchema(BaseModel):
    """A smart alternative candidate proposed after exact constraint failure."""
    relaxation_type: str = Field(
        description="'price_headroom' | 'timeline_extension' | 'cross_platform' | 'category_substitute'"
    )
    difference_explanation: str
    product: ProductSchema
    merchant_name: str
    merchant_type: str
    price_inr: float
    fulfillment_sla: str


class FailureDiagnosis(BaseModel):
    """Diagnostic classification of why a transaction or search failed."""
    failure_code: str  # "OUT_OF_STOCK" | "PRICE_SURGE" | "POLICY_BLOCKED" | "SLA_BREACH" | "NO_MATCH"
    human_explanation: str
    remediation_strategy: str


class RecoveryService:
    """Multi-Dimensional Constraint Relaxation and Smart Alternative Recovery Engine."""

    @staticmethod
    def diagnose_failure(
        status: str,
        error_details: list[str] | None = None,
        product_name: str | None = None,
    ) -> FailureDiagnosis:
        """Classifies a failure into structured diagnosis with remediation strategy."""
        errors_str = " ".join(error_details or []).lower()
        p_name = product_name or "The requested product"

        if "stock" in errors_str or "inventory" in errors_str:
            return FailureDiagnosis(
                failure_code="OUT_OF_STOCK",
                human_explanation=f"{p_name} is currently out of stock at this merchant.",
                remediation_strategy="Cross-platform search on Blinkit/Zepto or category substitutes.",
            )
        elif "price" in errors_str or "budget" in errors_str:
            return FailureDiagnosis(
                failure_code="PRICE_SURGE",
                human_explanation=f"{p_name} exceeds your specified budget ceiling.",
                remediation_strategy="Price headroom relaxation (+10-25%) or value-tier alternatives.",
            )
        elif "policy" in errors_str or "daily" in errors_str or status == "blocked":
            return FailureDiagnosis(
                failure_code="POLICY_BLOCKED",
                human_explanation="Transaction exceeds user spending limit or policy configuration.",
                remediation_strategy="Strict policy filtering or user policy adjustment.",
            )
        elif "sla" in errors_str or "time" in errors_str or "deadline" in errors_str:
            return FailureDiagnosis(
                failure_code="SLA_BREACH",
                human_explanation=f"Merchant preparation time cannot meet the specified delivery timeline.",
                remediation_strategy="Fulfillment SLA relaxation to standard delivery or pickup.",
            )
        else:
            return FailureDiagnosis(
                failure_code="NO_MATCH",
                human_explanation="No catalog item matched all criteria simultaneously.",
                remediation_strategy="4-dimensional constraint relaxation across platforms and categories.",
            )

    @staticmethod
    async def find_smart_alternatives(
        session: AsyncSession,
        intent: BuyerIntentSchema,
        failed_product_id: str | None = None,
        vector_service: VectorService | None = None,
        limit: int = 3,
    ) -> list[AlternativeOptionSchema]:
        """Finds smart, verified alternatives across 4 relaxation dimensions."""
        logger.info(
            "Searching smart alternatives with constraint relaxation",
            query=intent.product_query,
            budget=intent.max_price,
            pincode=intent.pincode,
        )

        alternatives: list[AlternativeOptionSchema] = []
        seen_product_ids: set[str] = set()
        if failed_product_id:
            seen_product_ids.add(failed_product_id)

        # 1. Fetch all active merchants map (merchant_id -> MerchantModel)
        stmt_m = select(MerchantModel).where(MerchantModel.is_active == True)
        res_m = await session.execute(stmt_m)
        merchants_map = {m.merchant_id: m for m in res_m.scalars().all()}

        # 2. Fetch all in-stock products in the area
        stmt_p = select(ProductModel).where(
            ProductModel.availability_status == AvailabilityStatus.IN_STOCK.value,
            ProductModel.quantity > 0,
        )
        if intent.pincode:
            stmt_p = stmt_p.where(
                (ProductModel.pincode == intent.pincode) | (ProductModel.pincode == None)
            )
        res_p = await session.execute(stmt_p)
        all_in_stock = res_p.scalars().all()

        query_lower = (intent.product_query or "").lower().strip()
        cat_val = intent.category.value if intent.category else None

        # --- Dimension 1: Cross-Platform / Cross-Merchant Switching ---
        # Look for the exact/similar product on other platforms (Zepto, Blinkit, Sharma Sweets)
        if query_lower:
            for p in all_in_stock:
                if p.product_id in seen_product_ids:
                    continue
                p_name_lower = p.name.lower()
                if any(w in p_name_lower for w in query_lower.split()):
                    # Check if within budget or slightly relaxed
                    budget_ok = intent.max_price is None or p.price_amount <= intent.max_price
                    if budget_ok:
                        merchant = merchants_map.get(p.merchant_id)
                        merch_name = merchant.name if merchant else "Verified Merchant"
                        merch_type = merchant.type if merchant else "enterprise"
                        schema = model_to_schema(p)
                        sla_str = f"{schema.fulfillment.prep_time_minutes} min delivery" if schema.fulfillment.type.value == "delivery" else f"Ready for pickup in {schema.fulfillment.prep_time_minutes} mins"
                        alternatives.append(
                            AlternativeOptionSchema(
                                relaxation_type="cross_platform",
                                difference_explanation=f"Available in-stock on {merch_name} for ₹{p.price_amount / 100:.2f}",
                                product=schema,
                                merchant_name=merch_name,
                                merchant_type=merch_type,
                                price_inr=p.price_amount / 100,
                                fulfillment_sla=sla_str,
                            )
                        )
                        seen_product_ids.add(p.product_id)
                        if len(alternatives) >= limit:
                            return alternatives

        # --- Dimension 2: Price Headroom (+10% to +30% Budget Relaxation) ---
        # If no items found within strict budget, look for matching item with slight headroom
        if intent.max_price and query_lower:
            relaxed_ceiling = int(intent.max_price * 1.30)  # +30% headroom
            for p in all_in_stock:
                if p.product_id in seen_product_ids:
                    continue
                p_name_lower = p.name.lower()
                if any(w in p_name_lower for w in query_lower.split()) and intent.max_price < p.price_amount <= relaxed_ceiling:
                    merchant = merchants_map.get(p.merchant_id)
                    merch_name = merchant.name if merchant else "Verified Merchant"
                    merch_type = merchant.type if merchant else "enterprise"
                    schema = model_to_schema(p)
                    diff_inr = (p.price_amount - intent.max_price) / 100
                    sla_str = f"{schema.fulfillment.prep_time_minutes} min delivery" if schema.fulfillment.type.value == "delivery" else f"Ready for pickup in {schema.fulfillment.prep_time_minutes} mins"
                    alternatives.append(
                        AlternativeOptionSchema(
                            relaxation_type="price_headroom",
                            difference_explanation=f"₹{diff_inr:.2f} above your budget (₹{p.price_amount / 100:.2f}), available via {merch_name}",
                            product=schema,
                            merchant_name=merch_name,
                            merchant_type=merch_type,
                            price_inr=p.price_amount / 100,
                            fulfillment_sla=sla_str,
                        )
                    )
                    seen_product_ids.add(p.product_id)
                    if len(alternatives) >= limit:
                        return alternatives

        # --- Dimension 3: Category Substitution (Same Category in-stock items) ---
        # If product is unavailable, find in-stock alternatives in same category
        for p in all_in_stock:
            if p.product_id in seen_product_ids:
                continue
            if cat_val and p.category == cat_val:
                # Within relaxed budget
                if intent.max_price is None or p.price_amount <= int(intent.max_price * 1.20):
                    merchant = merchants_map.get(p.merchant_id)
                    merch_name = merchant.name if merchant else "Verified Merchant"
                    merch_type = merchant.type if merchant else "local_merchant"
                    schema = model_to_schema(p)
                    sla_str = f"{schema.fulfillment.prep_time_minutes} min delivery" if schema.fulfillment.type.value == "delivery" else f"Ready for pickup in {schema.fulfillment.prep_time_minutes} mins"
                    alternatives.append(
                        AlternativeOptionSchema(
                            relaxation_type="category_substitute",
                            difference_explanation=f"Popular {p.category} alternative from {merch_name} for ₹{p.price_amount / 100:.2f}",
                            product=schema,
                            merchant_name=merch_name,
                            merchant_type=merch_type,
                            price_inr=p.price_amount / 100,
                            fulfillment_sla=sla_str,
                        )
                    )
                    seen_product_ids.add(p.product_id)
                    if len(alternatives) >= limit:
                        return alternatives

        # --- Dimension 4: Timeline / SLA Extension (Any remaining top in-stock items) ---
        for p in all_in_stock:
            if p.product_id in seen_product_ids:
                continue
            merchant = merchants_map.get(p.merchant_id)
            merch_name = merchant.name if merchant else "Verified Merchant"
            merch_type = merchant.type if merchant else "local_merchant"
            schema = model_to_schema(p)
            sla_str = f"{schema.fulfillment.prep_time_minutes} min delivery" if schema.fulfillment.type.value == "delivery" else f"Ready for pickup in {schema.fulfillment.prep_time_minutes} mins"
            alternatives.append(
                AlternativeOptionSchema(
                    relaxation_type="timeline_extension",
                    difference_explanation=f"In-stock option from {merch_name} ({sla_str})",
                    product=schema,
                    merchant_name=merch_name,
                    merchant_type=merch_type,
                    price_inr=p.price_amount / 100,
                    fulfillment_sla=sla_str,
                )
            )
            seen_product_ids.add(p.product_id)
            if len(alternatives) >= limit:
                break

        return alternatives
