from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.merchants import router as merchants_router
from app.api.v1.products import router as products_router
from app.api.v1.manifests import router as manifests_router
from app.api.v1.mcp import router as mcp_router
from app.api.v1.intent import router as intent_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.policies import router as policies_router
from app.api.v1.verification import router as verification_router
from app.api.v1.agent import router as agent_router
from app.api.v1.payments import router as payments_router
from app.api.v1.orders import router as orders_router
from app.api.v1.audit import router as audit_router
from app.api.v1.recovery import router as recovery_router
from app.api.v1.hosts import router as hosts_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(manifests_router)
api_v1_router.include_router(mcp_router)
api_v1_router.include_router(intent_router)
api_v1_router.include_router(discovery_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(verification_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(recovery_router)
api_v1_router.include_router(hosts_router)

__all__ = [
    "api_v1_router",
    "merchants_router",
    "products_router",
    "manifests_router",
    "mcp_router",
    "intent_router",
    "discovery_router",
    "policies_router",
    "verification_router",
    "agent_router",
    "payments_router",
    "orders_router",
    "audit_router",
    "recovery_router",
    "hosts_router",
]
