from __future__ import annotations

import logging
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas import ProductSchema

logger = get_logger(__name__)

class VectorService:
    """Service for handling vector embeddings and semantic search via Qdrant."""

    def __init__(
        self,
        qdrant_url: str | None = None,
        qdrant_api_key: str | None = None,
        collection_name: str = "products"
    ):
        """Initialize the VectorService."""
        self.collection_name = collection_name
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
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

    async def upsert_product(self, product: ProductSchema) -> None:
        """Generates embedding and upserts product into Qdrant."""
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
        """Deletes a product point from Qdrant by its ID."""
        try:
            point_id = self._normalize_point_id(product_id)
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
        """Searches for similar products in Qdrant with optional filters."""
        try:
            embeddings = list(self.embedder.embed([query]))
            query_vector = embeddings[0].tolist()

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


def get_vector_service() -> VectorService:
    """Factory to get the VectorService singleton instance."""
    settings = get_settings()
    return VectorService(
        qdrant_url=settings.QDRANT_URL,
        qdrant_api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION or "products"
    )
