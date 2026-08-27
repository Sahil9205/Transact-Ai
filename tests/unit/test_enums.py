from __future__ import annotations
import enum
from app.domain.enums import (
    ProviderType, ProductCategory, AvailabilityStatus,
    FulfillmentType, OrderStatus, PaymentStatus,
    FreshnessTier, AuditEventType
)

def test_enums_are_strings():
    for enum_class in [ProviderType, ProductCategory, AvailabilityStatus, FulfillmentType, OrderStatus, PaymentStatus, FreshnessTier, AuditEventType]:
        assert issubclass(enum_class, str)
        assert issubclass(enum_class, enum.Enum)

def test_order_status_values():
    assert OrderStatus.DISCOVERED == "discovered"
    assert OrderStatus.COMPLETED == "completed"

def test_freshness_tier_values():
    assert FreshnessTier.FRESH == "fresh"
    assert FreshnessTier.STALE == "stale"

def test_provider_type_values():
    assert ProviderType.LOCAL_MERCHANT == "local_merchant"
    assert ProviderType.ENTERPRISE == "enterprise"
