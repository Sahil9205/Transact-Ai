from __future__ import annotations
from abc import ABC, abstractmethod
from app.domain.schemas import (
    ProviderSchema, ProductSchema, PricingSchema, 
    AvailabilitySchema, ProductCreateSchema, ProductUpdateSchema
)


class BaseProviderAdapter(ABC):
    """Abstract adapter converting provider-specific data into canonical models.
    
    Every commerce provider (local merchant, Blinkit, Zepto, Amazon, etc.)
    must implement this interface. The Commerce Agent only interacts with
    this abstraction — never with provider-specific APIs directly.
    """

    @abstractmethod
    async def get_provider_info(self) -> ProviderSchema:
        """Get canonical provider information."""
        ...

    @abstractmethod
    async def search_products(
        self,
        query: str | None = None,
        category: str | None = None,
        pincode: str | None = None,
    ) -> list[ProductSchema]:
        """Search products with optional filters."""
        ...

    @abstractmethod
    async def get_product(self, product_id: str) -> ProductSchema | None:
        """Get a single product by ID. Returns None if not found."""
        ...

    @abstractmethod
    async def check_availability(self, product_id: str) -> AvailabilitySchema:
        """Check real-time availability for a product."""
        ...

    @abstractmethod
    async def get_current_price(self, product_id: str) -> PricingSchema:
        """Get the authoritative current price. This is the source of truth."""
        ...
