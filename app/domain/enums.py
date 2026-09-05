from __future__ import annotations
import enum

class ProviderType(str, enum.Enum):
    LOCAL_MERCHANT = "local_merchant"
    ENTERPRISE = "enterprise"
    MARKETPLACE = "marketplace"

class ProductCategory(str, enum.Enum):
    FOOD = "food"
    SWEETS = "sweets"
    GROCERIES = "groceries"
    BEVERAGES = "beverages"
    STATIONERY = "stationery"
    GENERAL = "general"

class AvailabilityStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LIMITED = "limited"

class FulfillmentType(str, enum.Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
    BOTH = "both"

class PricingType(str, enum.Enum):
    FIXED_UNIT = "fixed_unit"
    WEIGHT_BASED = "weight_based"
    VOLUME_BASED = "volume_based"

class StoreOperationalStatus(str, enum.Enum):
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"

class OrderStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    ORDER_CREATED = "order_created"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class FreshnessTier(str, enum.Enum):
    FRESH = "fresh"                    # < 1 hour
    STALE_WARNING = "stale_warning"    # 1-6 hours
    STALE = "stale"                    # > 6 hours

class AuditEventType(str, enum.Enum):
    INTENT_RECEIVED = "intent_received"
    DISCOVERY_STARTED = "discovery_started"
    CANDIDATE_FOUND = "candidate_found"
    VERIFICATION_STARTED = "verification_started"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    POLICY_CHECK_PASSED = "policy_check_passed"
    POLICY_CHECK_FAILED = "policy_check_failed"
    RECOMMENDATION_CREATED = "recommendation_created"
    USER_CONFIRMATION = "user_confirmation"
    FINAL_REVALIDATION = "final_revalidation"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    ORDER_CREATED = "order_created"
    NOTIFICATION_SENT = "notification_sent"
