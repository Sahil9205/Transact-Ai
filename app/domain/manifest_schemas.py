from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import FreshnessTier, ProviderType


class CapabilitySchema(BaseModel):
    """Fulfillment and ordering capabilities of a merchant."""
    can_pickup: bool = Field(default=True, description="Supports in-store / local pickup")
    can_deliver: bool = Field(default=False, description="Supports direct delivery")
    delivery_pincodes: list[str] = Field(default_factory=list, description="List of serviceable pincodes")
    avg_prep_time_minutes: int = Field(default=15, ge=0, description="Average order preparation time in minutes")
    slot_capacity: int | None = Field(default=None, ge=0, description="Maximum concurrent order capacity")


class PolicySummarySchema(BaseModel):
    """Commerce and transaction policies for the merchant."""
    cancellation_allowed: bool = Field(default=True, description="Whether order cancellation is permitted")
    cancellation_window_minutes: int = Field(default=5, ge=0, description="Allowed cancellation window before preparation starts")
    return_policy: str = Field(default="No returns on perishable food items once delivered.", description="Summary of return policy")
    accepted_currencies: list[str] = Field(default_factory=lambda: ["INR"], description="Currencies accepted")
    payment_methods: list[str] = Field(
        default_factory=lambda: ["razorpay_upi", "razorpay_card", "razorpay_netbanking"],
        description="Supported payment methods through Razorpay",
    )


class CategorySummarySchema(BaseModel):
    """Aggregated catalog metrics for a specific product category."""
    category: str
    product_count: int = Field(ge=0, description="Total active products in category")
    min_price_amount: int = Field(ge=0, description="Minimum item price in category (in paise)")
    max_price_amount: int = Field(ge=0, description="Maximum item price in category (in paise)")
    currency: str = Field(default="INR")


class AgentToolDescriptorSchema(BaseModel):
    """Machine-readable tool declaration for external AI agents."""
    name: str = Field(description="Tool identifier matching AI agent function call")
    description: str = Field(description="Natural language description of what this tool performs")
    parameters: dict[str, Any] = Field(description="JSON schema describing tool arguments")
    endpoint_url: str = Field(description="API endpoint path for the tool")
    http_method: str = Field(default="GET", description="HTTP method required")


class MerchantManifestSchema(BaseModel):
    """Full agent-readable manifest for a specific merchant."""
    manifest_version: str = Field(default="1.0.0", description="Manifest format specification version")
    generated_at: datetime = Field(description="UTC timestamp when this manifest was compiled")
    freshness_tier: FreshnessTier = Field(description="Deterministic freshness grade of the catalog")
    provider_id: str = Field(description="Unique merchant provider UUID")
    name: str = Field(description="Merchant legal or trade name")
    type: ProviderType = Field(description="Provider classification")
    description: str | None = Field(default=None, description="Merchant bio / profile description")
    location: str | None = Field(default=None, description="Physical store address or dark store hub")
    pincode: str | None = Field(default=None, description="Primary location pincode")
    capabilities: CapabilitySchema = Field(description="Fulfillment SLAs and capacities")
    policies: PolicySummarySchema = Field(description="Cancellation, payment, and refund policies")
    categories: list[CategorySummarySchema] = Field(default_factory=list, description="Category distribution and price spans")
    total_active_products: int = Field(ge=0, description="Total number of items in active catalog")
    available_tools: list[AgentToolDescriptorSchema] = Field(default_factory=list, description="Actionable tools exposed to AI agents")


class ConnectedMerchantSummary(BaseModel):
    """Brief merchant summary for global directory manifest."""
    provider_id: str
    name: str
    type: ProviderType
    location: str | None = None
    pincode: str | None = None
    category_names: list[str] = Field(default_factory=list)
    product_count: int = 0
    manifest_url: str


class GlobalDirectoryManifestSchema(BaseModel):
    """System-wide manifest listing all connected commerce providers."""
    manifest_version: str = Field(default="1.0.0", description="Global manifest specification version")
    generated_at: datetime = Field(description="Compilation timestamp")
    total_merchants: int = Field(ge=0, description="Total active registered merchants")
    total_products: int = Field(ge=0, description="Total active products across all merchants")
    supported_pincodes: list[str] = Field(default_factory=list, description="Combined unique serviceable pincodes")
    all_categories: list[str] = Field(default_factory=list, description="All distinct categories available")
    merchants: list[ConnectedMerchantSummary] = Field(default_factory=list, description="List of connected merchant manifests")
