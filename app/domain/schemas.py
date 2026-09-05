from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import (
    ProviderType, ProductCategory, AvailabilityStatus,
    FulfillmentType, OrderStatus, PaymentStatus,
    FreshnessTier, AuditEventType, PricingType, StoreOperationalStatus
)

# Value objects (never standalone DB entities)
class PricingSchema(BaseModel):
    """Pricing information. Amount is in paise (smallest currency unit)."""
    amount: int = Field(ge=0, description="Price in paise. ₹450 = 45000")
    currency: str = Field(default="INR")
    pricing_type: PricingType = Field(default=PricingType.FIXED_UNIT)
    unit: str = Field(default="piece", description="kg, g, piece, liter, pack")
    min_quantity: float = Field(default=1.0, gt=0, description="Minimum orderable quantity")
    increment_step: float = Field(default=1.0, gt=0, description="Step quantity e.g. 0.25 kg")

class AvailabilitySchema(BaseModel):
    """Product availability status."""
    status: AvailabilityStatus
    quantity: int | None = Field(default=None, ge=0)

class FulfillmentSchema(BaseModel):
    """Fulfillment/delivery information."""
    type: FulfillmentType
    prep_time_minutes: int = Field(ge=0)
    slot_capacity: int | None = Field(default=None, ge=0)

class VerificationSchema(BaseModel):
    """Data freshness verification metadata."""
    last_verified: datetime
    freshness_tier: FreshnessTier

# Main entities
class ProviderSchema(BaseModel):
    """Canonical representation of a commerce provider."""
    model_config = ConfigDict(from_attributes=True)
    
    provider_id: str
    name: str
    type: ProviderType
    description: str | None = None
    location: str | None = None
    pincode: str | None = None
    is_active: bool = True
    api_key: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    business_type: str | None = None
    onboarding_status: str | None = "active"
    operational_status: StoreOperationalStatus | str = "open"
    logo_url: str | None = None

class ProductSchema(BaseModel):
    """Canonical representation of a product across all provider types."""
    model_config = ConfigDict(from_attributes=True)
    
    product_id: str
    provider_id: str
    name: str
    description: str | None = None
    category: ProductCategory
    pricing: PricingSchema
    availability: AvailabilitySchema
    fulfillment: FulfillmentSchema
    location: str | None = None
    pincode: str | None = None
    verification: VerificationSchema

class BuyerIntentSchema(BaseModel):
    """Structured buyer intent parsed from natural language."""
    product_query: str
    max_price: int | None = Field(default=None, ge=0, description="Max price in paise")
    currency: str = "INR"
    deadline: str | None = Field(default=None, description="Deadline in HH:MM format")
    category: ProductCategory | None = None
    pincode: str | None = None

class SpendingPolicySchema(BaseModel):
    """User-level transaction spending policy."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    max_per_transaction: int = Field(ge=0, description="Max per transaction in paise")
    daily_limit: int = Field(ge=0, description="Daily spending limit in paise")
    allowed_categories: list[ProductCategory]
    is_active: bool = True

# Create/Update DTOs
class ProviderCreateSchema(BaseModel):
    """Schema for creating a new provider."""
    name: str
    type: ProviderType
    description: str | None = None
    location: str | None = None
    pincode: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    business_type: str | None = None
    logo_url: str | None = None

class ProviderUpdateSchema(BaseModel):
    """Schema for updating an existing provider."""
    name: str | None = None
    description: str | None = None
    location: str | None = None
    pincode: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    business_type: str | None = None
    onboarding_status: str | None = None
    operational_status: StoreOperationalStatus | str | None = None
    is_active: bool | None = None

class ProductCreateSchema(BaseModel):
    """Schema for creating/registering a new product."""
    name: str
    description: str | None = None
    category: ProductCategory
    price_amount: int = Field(ge=0, description="Price in paise")
    price_currency: str = "INR"
    pricing_type: PricingType = PricingType.FIXED_UNIT
    unit: str = "piece"
    min_quantity: float = Field(default=1.0, gt=0)
    increment_step: float = Field(default=1.0, gt=0)
    quantity: int = Field(default=0, ge=0)
    availability_status: AvailabilityStatus = AvailabilityStatus.IN_STOCK
    fulfillment_type: FulfillmentType = FulfillmentType.PICKUP
    prep_time_minutes: int = Field(ge=0, default=0)
    slot_capacity: int | None = None
    pincode: str | None = None

class ProductUpdateSchema(BaseModel):
    """Schema for updating product fields. All fields optional."""
    name: str | None = None
    price_amount: int | None = Field(default=None, ge=0)
    pricing_type: PricingType | None = None
    unit: str | None = None
    min_quantity: float | None = Field(default=None, gt=0)
    increment_step: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=0)
    availability_status: AvailabilityStatus | None = None
    prep_time_minutes: int | None = Field(default=None, ge=0)
    slot_capacity: int | None = Field(default=None, ge=0)
