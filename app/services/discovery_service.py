from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import ProductModel
from app.db.repository import MerchantRepository, ProductRepository
from app.domain.enums import FreshnessTier
from app.domain.schemas import BuyerIntentSchema, ProductSchema
from app.services.product_service import model_to_schema
from app.services.vector_service import VectorService

logger = get_logger(__name__)


class RankedCandidateSchema(BaseModel):
    """A scored and ranked candidate product match from discovery."""
    rank: int
    score: float = Field(ge=0.0, le=1.0)
    recommendation_tag: str
    product: ProductSchema
    merchant_name: str
    merchant_type: str
    price_inr: float
    savings_vs_budget_inr: float | None = None
    fulfillment_sla: str


class DiscoveryService:
    """Multi-provider hybrid semantic discovery and deterministic ranking engine."""

    @staticmethod
    async def match_candidates(
        session: AsyncSession,
        intent: BuyerIntentSchema,
        vector_service: VectorService | None = None,
    ) -> list[RankedCandidateSchema]:
        """Performs hybrid semantic search + DB search across all providers and ranks matches deterministically."""
        logger.info(
            "Executing hybrid discovery",
            query=intent.product_query,
            max_price=intent.max_price,
            category=intent.category.value if intent.category else None,
            pincode=intent.pincode,
        )

        candidate_map: dict[str, tuple[ProductModel, float]] = {}  # product_id -> (ProductModel, semantic_score)

        # Dynamically resolve location/pincode from database if not explicitly set as 6-digit numeric pincode
        if not intent.pincode and intent.product_query:
            db_pincode = await MerchantRepository.resolve_pincode_from_db(session, intent.product_query)
            if db_pincode:
                intent.pincode = db_pincode
                logger.info("Dynamically resolved pincode from database", pincode=db_pincode, query=intent.product_query)

        # 1 & 2. Concurrent Parallel Search: Fast In-Memory Vector Search + Relational DB Search
        async def _run_vector_search() -> list[dict[str, Any]]:
            if vector_service and intent.product_query:
                try:
                    return await vector_service.search_similar(
                        query=intent.product_query,
                        limit=10,
                        category=intent.category.value if intent.category else None,
                        max_price=intent.max_price,
                        pincode=intent.pincode,
                    )
                except Exception as e:
                    logger.warning(f"Vector discovery pass failed (continuing with DB pass): {e}")
            return []

        async def _run_db_search() -> list[ProductModel]:
            return await ProductRepository.search(
                session=session,
                query=intent.product_query,
                category=intent.category.value if intent.category else None,
                pincode=intent.pincode,
            )

        import asyncio
        vector_results, db_products = await asyncio.gather(
            _run_vector_search(),
            _run_db_search(),
        )

        # Merge results into candidate_map
        for p in db_products:
            candidate_map[p.product_id] = (p, 0.75)

        # For vector results, batch fetch any product models not yet loaded
        missing_ids = [
            hit.get("product_id") for hit in vector_results 
            if hit.get("product_id") and hit.get("product_id") not in candidate_map
        ]
        if missing_ids:
            fetched_models = await ProductRepository.get_by_product_ids(session, missing_ids)
            fetched_dict = {p.product_id: p for p in fetched_models}
            for hit in vector_results:
                pid = hit.get("product_id")
                if pid and pid in fetched_dict:
                    candidate_map[pid] = (fetched_dict[pid], float(hit.get("score", 0.85)))
        else:
            for hit in vector_results:
                pid = hit.get("product_id")
                if pid and pid in candidate_map:
                    p_model, _ = candidate_map[pid]
                    candidate_map[pid] = (p_model, float(hit.get("score", 0.85)))

        if not candidate_map and intent.category:
            # Fallback category search if keyword was too specific
            category_products = await ProductRepository.search(
                session=session,
                category=intent.category.value,
                pincode=intent.pincode,
            )
            for p in category_products:
                if p.product_id not in candidate_map:
                    candidate_map[p.product_id] = (p, 0.60)

        # 3. Apply Hard Deterministic Constraint Filters
        filtered_candidates: list[tuple[ProductModel, float]] = []
        for prod_id, (prod_model, sem_score) in candidate_map.items():
            # Filter A: Price Ceiling (Hard Reject if price > budget)
            if intent.max_price is not None and prod_model.price_amount > intent.max_price:
                continue

            # Filter B: Stock Availability
            if prod_model.availability_status != "in_stock" or prod_model.quantity <= 0:
                continue

            # Filter C: Pincode Location Match
            if intent.pincode and prod_model.pincode and prod_model.pincode != intent.pincode:
                continue

            filtered_candidates.append((prod_model, sem_score))

        if not filtered_candidates:
            return []

        # Batch fetch all unique merchants in a SINGLE SQL query (eliminates N+1 query loop!)
        unique_merchant_ids = list({pm.merchant_id for pm, _ in filtered_candidates})
        merchant_lookup = await MerchantRepository.get_by_merchant_ids(session, unique_merchant_ids)

        valid_candidates: list[tuple[ProductSchema, str, str, float]] = []
        for prod_model, sem_score in filtered_candidates:
            merchant = merchant_lookup.get(prod_model.merchant_id)
            merch_name = merchant.name if merchant else "Unknown Merchant"
            merch_type = merchant.type if merchant else "local_merchant"
            schema = model_to_schema(prod_model)
            valid_candidates.append((schema, merch_name, merch_type, sem_score))

        if not valid_candidates:
            return []

        # 4. Multi-Factor Deterministic Scoring
        # Find min price and min prep time for relative scaling
        prices = [c[0].pricing.amount for c in valid_candidates]
        min_price = min(prices) if prices else 1

        scored_candidates: list[tuple[float, str, ProductSchema, str, str]] = []
        for schema, merch_name, merch_type, sem_score in valid_candidates:
            # Score Component A: Semantic Fit (0.0 to 1.0)
            norm_sem = min(max(sem_score, 0.0), 1.0)

            # Score Component B: Price Value (Cheaper = higher score)
            if intent.max_price and intent.max_price > 0:
                price_score = 1.0 - (schema.pricing.amount / intent.max_price) * 0.5
            else:
                price_score = min_price / max(schema.pricing.amount, 1)

            # Score Component C: Speed SLA (Faster prep/delivery = higher score)
            prep_time = schema.fulfillment.prep_time_minutes
            speed_score = max(0.0, 1.0 - (prep_time / 60.0))

            # Score Component D: Data Freshness
            freshness_map = {
                FreshnessTier.FRESH: 1.0,
                FreshnessTier.STALE_WARNING: 0.5,
                FreshnessTier.STALE: 0.1,
            }
            freshness_score = freshness_map.get(schema.verification.freshness_tier, 0.5)

            # Composite Score Formula
            composite_score = round(
                0.40 * norm_sem + 0.30 * price_score + 0.20 * speed_score + 0.10 * freshness_score,
                4,
            )

            # Assign Recommendation Tag
            tag = "Recommended Option"
            if schema.pricing.amount == min_price and prep_time <= 10:
                tag = "⚡ Cheapest & Fastest"
            elif schema.pricing.amount == min_price:
                tag = "💰 Best Price"
            elif prep_time <= 10:
                tag = "⚡ Lightning Fast Delivery"
            elif merch_type == "local_merchant":
                tag = "🏪 Local Shop Favorite"

            scored_candidates.append((composite_score, tag, schema, merch_name, merch_type))

        # 5. Sort Descending by Composite Score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # 6. Build Final Ranked Output
        ranked_output: list[RankedCandidateSchema] = []
        for idx, (score, tag, schema, merch_name, merch_type) in enumerate(scored_candidates, start=1):
            savings = None
            if intent.max_price:
                savings = round((intent.max_price - schema.pricing.amount) / 100, 2)

            fulfillment_sla = (
                f"{schema.fulfillment.prep_time_minutes} min delivery"
                if schema.fulfillment.type.value == "delivery"
                else f"Ready for pickup in {schema.fulfillment.prep_time_minutes} mins"
            )

            ranked_output.append(
                RankedCandidateSchema(
                    rank=idx,
                    score=score,
                    recommendation_tag=tag,
                    product=schema,
                    merchant_name=merch_name,
                    merchant_type=merch_type,
                    price_inr=schema.pricing.amount / 100,
                    savings_vs_budget_inr=savings,
                    fulfillment_sla=fulfillment_sla,
                )
            )

        return ranked_output
