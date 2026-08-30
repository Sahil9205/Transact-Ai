from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.domain.manifest_schemas import (
    GlobalDirectoryManifestSchema,
    MerchantManifestSchema,
)
from app.services.manifest_service import ManifestService

router = APIRouter(tags=["Manifests"])


@router.get(
    "/manifest.json",
    response_model=GlobalDirectoryManifestSchema,
    summary="Global Directory Manifest",
    description="Returns the system-wide manifest indexing all active connected merchants, supported pincodes, and categories for AI host discovery.",
)
@router.get(
    "/manifests",
    response_model=GlobalDirectoryManifestSchema,
    include_in_schema=False,
)
async def get_global_manifest(
    session: AsyncSession = Depends(get_db),
) -> GlobalDirectoryManifestSchema:
    """Fetch global directory manifest."""
    return await ManifestService.generate_global_manifest(session)


@router.get(
    "/merchants/{merchant_id}/manifest.json",
    response_model=MerchantManifestSchema,
    summary="Merchant Agent Manifest",
    description="Returns full machine-readable manifest for a specific merchant including SLAs, category breakdown, policies, and AI agent tool definitions.",
)
async def get_merchant_manifest(
    merchant_id: str,
    session: AsyncSession = Depends(get_db),
) -> MerchantManifestSchema:
    """Fetch specific merchant agent manifest."""
    return await ManifestService.generate_merchant_manifest(session, merchant_id)


@router.get(
    "/merchants/{merchant_id}/schema.jsonld",
    response_model=dict[str, Any],
    summary="Merchant Schema.org JSON-LD",
    description="Returns standard Schema.org Store and Product offer JSON-LD metadata for semantic crawlers and AI agents.",
)
async def get_merchant_schema_jsonld(
    merchant_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Fetch Schema.org JSON-LD structured data for a merchant."""
    return await ManifestService.generate_schema_org_jsonld(session, merchant_id)
