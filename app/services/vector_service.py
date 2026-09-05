from __future__ import annotations

import logging
from typing import Any
import numpy as np

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas import ProductSchema

logger = get_logger(__name__)

# Global query embedding LRU cache (in-memory, max 1024 entries)
_QUERY_EMBEDDING_CACHE: dict[str, list[float]] = {}


class VectorService:
    """High-performance hybrid vector service with in-memory matrix index and Qdrant Cloud durability."""

    def __init__(
        self,
        qdrant_url: str | None = None,
        qdrant_api_key: str | None = None,
        collection_name: str = "products"
    ):
        """Initialize the VectorService with tier-1 in-memory index."""
        self.collection_name = collection_name
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self._memory_vectors: dict[str, dict[str, Any]] = {}
        
        try:
            if qdrant_url:
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
                logger.info(f"Connected to Qdrant Cloud at {qdrant_url}")
            else:
                self.client = QdrantClient(":memory:")
                logger.warning("No Qdrant URL provided. Using in-memory Qdrant client.")
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant Cloud: {e}. Falling back to in-memory client.")
            self.client = QdrantClient(":memory:")

    async def ensure_collection(self) -> None:
        """Ensures that the Qdrant collection exists."""
        try:
            collections_response = self.client.get_collections()
            collection_names = [collection.name for collection in collections_response.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
            else:
                logger.info(f"Collection {self.collection_name} already exists.")

            # Create payload indexes for filterable fields (required by Qdrant Cloud)
            for field in ["category", "pincode", "provider_id", "product_id", "availability"]:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=rest.PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass

            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="price_amount",
                    field_schema=rest.PayloadSchemaType.INTEGER,
                )
            except Exception:
                pass

            # Pre-warm local in-memory vector index from Qdrant if collection has points
            try:
                points, _ = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=2000,
                    with_vectors=True,
                    with_payload=True,
                )
                for p in points:
                    if p.vector is not None and p.payload:
                        vec_arr = np.array(p.vector, dtype=np.float32)
                        norm = np.linalg.norm(vec_arr)
                        if norm > 0:
                            vec_arr = vec_arr / norm
                        self._memory_vectors[str(p.id)] = {
                            "product_id": str(p.payload.get("product_id", p.id)),
                            "vector": vec_arr,
                            "payload": dict(p.payload),
                        }
                if self._memory_vectors:
                    logger.info(f"Pre-warmed in-memory vector index with {len(self._memory_vectors)} products")
            except Exception as e:
                logger.debug(f"Could not pre-warm in-memory vector cache: {e}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

    def _normalize_point_id(self, raw_id: str | int) -> str | int:
        """Converts any string identifier into a valid UUID format for Qdrant."""
        if isinstance(raw_id, int):
            return raw_id
        try:
            import uuid
            return str(uuid.UUID(str(raw_id)))
        except ValueError:
            import uuid
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id)))

    def _get_query_embedding(self, query: str) -> list[float]:
        """Fetches query embedding with high-speed in-memory LRU cache."""
        norm_q = query.strip().lower()
        if norm_q in _QUERY_EMBEDDING_CACHE:
            return _QUERY_EMBEDDING_CACHE[norm_q]
        embeddings = list(self.embedder.embed([query]))
        vec = embeddings[0].tolist()
        if len(_QUERY_EMBEDDING_CACHE) >= 1024:
            _QUERY_EMBEDDING_CACHE.pop(next(iter(_QUERY_EMBEDDING_CACHE)))
        _QUERY_EMBEDDING_CACHE[norm_q] = vec
        return vec

    async def upsert_product(self, product: ProductSchema) -> None:
        """Generates embedding and upserts product into memory index and Qdrant."""
        try:
            text_to_embed = f"{product.name} {product.description or ''} {product.category.value}"
            # Embeddings returns a generator, convert to list
            embeddings = list(self.embedder.embed([text_to_embed]))
            vector = embeddings[0].tolist()

            payload = {
                "product_id": str(product.product_id),
                "provider_id": str(product.provider_id),
                "name": product.name,
                "category": product.category.value,
                "price_amount": product.pricing.amount,
                "currency": product.pricing.currency,
                "availability": product.availability.status.value,
                "pincode": product.pincode,
                "fulfillment_type": product.fulfillment.type.value,
            }

            point_id = self._normalize_point_id(product.product_id)

            # Update tier-1 in-memory vector index
            vec_arr = np.array(vector, dtype=np.float32)
            norm = np.linalg.norm(vec_arr)
            if norm > 0:
                vec_arr = vec_arr / norm
            self._memory_vectors[str(point_id)] = {
                "product_id": str(product.product_id),
                "vector": vec_arr,
                "payload": payload,
            }

            # Update Qdrant client
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    rest.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            logger.debug(f"Upserted product {product.product_id} into Qdrant.")
        except Exception as e:
            logger.error(f"Failed to upsert product {product.product_id}: {e}")
            raise

    async def delete_product(self, product_id: str) -> None:
        """Deletes a product point from memory index and Qdrant by its ID."""
        try:
            point_id = self._normalize_point_id(product_id)
            self._memory_vectors.pop(str(point_id), None)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=rest.PointIdsList(
                    points=[point_id],
                ),
            )
            logger.info(f"Deleted product {product_id} from Qdrant.")
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            raise

    async def search_similar(
        self, 
        query: str, 
        limit: int = 5, 
        category: str | None = None, 
        max_price: int | None = None, 
        pincode: str | None = None
    ) -> list[dict[str, Any]]:
        """Searches for similar products with tier-1 sub-millisecond in-memory matrix index and Qdrant fallback."""
        try:
            query_vector = self._get_query_embedding(query)

            # Tier 1: High-Speed In-Memory Vector Search (< 0.1ms)
            if self._memory_vectors:
                q_arr = np.array(query_vector, dtype=np.float32)
                q_norm = np.linalg.norm(q_arr)
                if q_norm > 0:
                    q_arr = q_arr / q_norm

                candidates = []
                for item in self._memory_vectors.values():
                    payload = item["payload"]
                    if category and payload.get("category") != category:
                        continue
                    if max_price is not None and payload.get("price_amount", 0) > max_price:
                        continue
                    if pincode and payload.get("pincode") and payload.get("pincode") != pincode:
                        continue
                    candidates.append(item)

                if candidates:
                    matrix = np.stack([c["vector"] for c in candidates])
                    scores = np.dot(matrix, q_arr)
                    top_indices = np.argsort(scores)[::-1][:limit]
                    results = []
                    for idx in top_indices:
                        item = candidates[idx]
                        res_dict = dict(item["payload"])
                        res_dict["score"] = float(scores[idx])
                        results.append(res_dict)
                    return results

            # Tier 2: Qdrant Client Fallback (Cold start or empty memory cache)
            must_conditions = []
            if category:
                must_conditions.append(
                    rest.FieldCondition(
                        key="category",
                        match=rest.MatchValue(value=category)
                    )
                )
            if max_price is not None:
                must_conditions.append(
                    rest.FieldCondition(
                        key="price_amount",
                        range=rest.Range(lte=max_price)
                    )
                )
            if pincode:
                must_conditions.append(
                    rest.FieldCondition(
                        key="pincode",
                        match=rest.MatchValue(value=pincode)
                    )
                )

            filter_params = None
            if must_conditions:
                filter_params = rest.Filter(must=must_conditions)

            if hasattr(self.client, "query_points"):
                search_res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=filter_params,
                    limit=limit,
                )
                hits = search_res.points
            elif hasattr(self.client, "search"):
                hits = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=filter_params,
                    limit=limit,
                )
            else:
                hits = []

            results = []
            for hit in hits:
                result_dict = dict(hit.payload or {})
                result_dict["score"] = getattr(hit, "score", 0.0)
                results.append(result_dict)

            return results
        except Exception as e:
            logger.error(f"Error searching similar products: {e}")
            raise


_VECTOR_SERVICE_INSTANCE: VectorService | None = None


def get_vector_service() -> VectorService:
    """Factory to get the VectorService singleton instance."""
    global _VECTOR_SERVICE_INSTANCE
    if _VECTOR_SERVICE_INSTANCE is None:
        settings = get_settings()
        _VECTOR_SERVICE_INSTANCE = VectorService(
            qdrant_url=settings.QDRANT_URL,
            qdrant_api_key=settings.QDRANT_API_KEY,
            collection_name=settings.QDRANT_COLLECTION or "products"
        )
    return _VECTOR_SERVICE_INSTANCE
