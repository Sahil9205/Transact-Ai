from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.merchants import router as merchants_router
from app.api.v1.products import router as products_router
from app.api.v1.manifests import router as manifests_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(manifests_router)

__all__ = ["api_v1_router", "merchants_router", "products_router", "manifests_router"]
