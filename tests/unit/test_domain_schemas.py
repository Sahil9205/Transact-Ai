from __future__ import annotations
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.domain.enums import ProviderType, ProductCategory, AvailabilityStatus, FulfillmentType, FreshnessTier
from app.domain.schemas import (
    ProviderSchema, ProductSchema, BuyerIntentSchema, SpendingPolicySchema,
    ProductCreateSchema, PricingSchema, AvailabilitySchema, FulfillmentSchema, VerificationSchema
)

def test_product_schema_creation():
    product = ProductSchema(
        product_id="prod_1",
        provider_id="prov_1",
        name="Test",
        category=ProductCategory.FOOD,
        pricing=PricingSchema(amount=100, currency="INR"),
        availability=AvailabilitySchema(status=AvailabilityStatus.IN_STOCK),
        fulfillment=FulfillmentSchema(type=FulfillmentType.PICKUP, prep_time_minutes=10),
        verification=VerificationSchema(last_verified=datetime.now(timezone.utc), freshness_tier=FreshnessTier.FRESH)
    )
    assert product.name == "Test"

def test_pricing_schema_validation():
    with pytest.raises(ValidationError):
        PricingSchema(amount=-10)
    PricingSchema(amount=0)

def test_buyer_intent_schema():
    intent = BuyerIntentSchema(product_query="test")
    assert intent.max_price is None
    intent_with_price = BuyerIntentSchema(product_query="test", max_price=100)
    assert intent_with_price.max_price == 100

def test_provider_schema_from_attributes():
    class DummyProvider:
        provider_id = "prov_1"
        name = "Prov"
        type = ProviderType.LOCAL_MERCHANT
        description = None
        location = None
        pincode = None
        is_active = True
        
    prov = ProviderSchema.model_validate(DummyProvider())
    assert prov.name == "Prov"

def test_product_create_schema_validation():
    with pytest.raises(ValidationError):
        ProductCreateSchema(name="Test", category=ProductCategory.FOOD, price_amount=-10, quantity=1)

def test_spending_policy_schema():
    policy = SpendingPolicySchema(
        user_id="user_1",
        max_per_transaction=1000,
        daily_limit=5000,
        allowed_categories=[ProductCategory.FOOD]
    )
    assert policy.daily_limit == 5000
