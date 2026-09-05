from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class MerchantModel(Base):
    __tablename__ = "merchants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # ProviderType value
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    api_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: f"sk_live_{uuid.uuid4().hex}")
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default="general")
    onboarding_status: Mapped[str] = mapped_column(String(30), default="active")
    operational_status: Mapped[str] = mapped_column(String(30), default="open")  # open, paused, closed
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    products: Mapped[list[ProductModel]] = relationship(back_populates="merchant", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Merchant {self.name} ({self.merchant_id}) status={self.onboarding_status}>"


class ProductModel(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ProductCategory value
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise
    price_currency: Mapped[str] = mapped_column(String(3), default="INR")
    pricing_type: Mapped[str] = mapped_column(String(30), default="fixed_unit")  # fixed_unit, weight_based, volume_based
    unit: Mapped[str] = mapped_column(String(20), default="piece")  # piece, kg, g, liter, pack
    min_quantity: Mapped[float] = mapped_column(Float, default=1.0)
    increment_step: Mapped[float] = mapped_column(Float, default=1.0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    availability_status: Mapped[str] = mapped_column(String(50), default="in_stock")
    fulfillment_type: Mapped[str] = mapped_column(String(50), default="pickup")
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    slot_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_verified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    merchant: Mapped[MerchantModel] = relationship(back_populates="products", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Product {self.name} ({self.product_id})>"


class UserModel(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<User {self.name} ({self.user_id})>"


class SpendingPolicyModel(Base):
    __tablename__ = "spending_policies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    max_per_transaction: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    allowed_categories: Mapped[dict | list] = mapped_column(JSON, default=list)  # list of category strings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<SpendingPolicy user={self.user_id} limit={self.daily_limit}>"


class OrderModel(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(String(50), default="discovered")  # OrderStatus value
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<Order {self.order_id} status={self.status} platform={self.platform}>"


class PaymentModel(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.order_id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # PaymentStatus value
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Razorpay payment_id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<Payment {self.payment_id} status={self.status}>"


class AuditEventModel(Base):
    __tablename__ = "audit_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # AuditEventType value
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # flexible context
    
    def __repr__(self) -> str:
        return f"<AuditEvent {self.event_type} at {self.timestamp}>"
