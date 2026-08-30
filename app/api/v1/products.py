from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.schemas import (
    ProductCreateSchema,
    ProductSchema,
    ProductUpdateSchema,
)
from app.services.product_service import ProductService
from app.services.vector_service import VectorService, get_vector_service

router = APIRouter(tags=["Products"])


def get_vector_service_dep(request: Request) -> VectorService:
    """Dependency helper to get the VectorService from app state."""
    if hasattr(request.app.state, "vector_service") and request.app.state.vector_service is not None:
        return request.app.state.vector_service
    return get_vector_service()


@router.post(
    "/merchants/{merchant_id}/products",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add product to merchant catalog",
    description="Registers a new product under the specified merchant, auto-generates vector embedding in Qdrant, and logs the audit event.",
)
async def add_product(
    merchant_id: str,
    data: ProductCreateSchema,
    session: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service_dep),
) -> ProductSchema:
    """Add a product to a merchant's catalog."""
    return await ProductService.add_product(
        session=session,
        merchant_id=merchant_id,
        data=data,
        vector_service=vector_service,
    )


@router.get(
    "/merchants/{merchant_id}/products",
    response_model=list[ProductSchema],
    summary="List products for a merchant",
    description="Fetches all products registered under a specific merchant.",
)
async def list_merchant_products(
    merchant_id: str,
    session: AsyncSession = Depends(get_db),
) -> list[ProductSchema]:
    """List all products for a specific merchant."""
    return await ProductService.search_products(session=session, merchant_id=merchant_id)


@router.get(
    "/products/search",
    response_model=list[ProductSchema],
    summary="Search products across providers",
    description="Searches products across all providers with optional filters (query, category, pincode, merchant_id).",
)
async def search_products(
    q: str | None = Query(default=None, description="Search query term for product name"),
    category: str | None = Query(default=None, description="Product category filter"),
    pincode: str | None = Query(default=None, description="Pincode location filter"),
    merchant_id: str | None = Query(default=None, description="Merchant UUID filter"),
    session: AsyncSession = Depends(get_db),
) -> list[ProductSchema]:
    """Search products across providers."""
    return await ProductService.search_products(
        session=session,
        query=q,
        category=category,
        pincode=pincode,
        merchant_id=merchant_id,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductSchema,
    summary="Get product by ID",
    description="Fetches detailed canonical information for a specific product by its unique product_id UUID.",
)
async def get_product(
    product_id: str,
    session: AsyncSession = Depends(get_db),
) -> ProductSchema:
    """Get single product details."""
    return await ProductService.get_product(session=session, product_id=product_id)


@router.patch(
    "/products/{product_id}",
    response_model=ProductSchema,
    summary="Update product details",
    description="Updates product pricing, inventory quantity, availability, or fulfillment parameters, re-indexes in Qdrant, and logs the revalidation event.",
)
async def update_product(
    product_id: str,
    data: ProductUpdateSchema,
    session: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service_dep),
) -> ProductSchema:
    """Update a product's details and price/inventory."""
    return await ProductService.update_product(
        session=session,
        product_id=product_id,
        data=data,
        vector_service=vector_service,
    )
