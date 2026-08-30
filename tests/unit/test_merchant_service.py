from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ProviderType
from app.domain.schemas import ProviderCreateSchema
from app.services.merchant_service import MerchantService
from app.core.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_register_and_get_merchant(db_session: AsyncSession) -> None:
    """Test registering a new merchant and retrieving it."""
    data = ProviderCreateSchema(
        name="Test Sweets",
        type=ProviderType.LOCAL_MERCHANT,
        description="Fresh Indian sweets",
        location="Sector 18, Noida",
        pincode="201301",
    )
    
    merchant = await MerchantService.register_merchant(db_session, data)
    assert merchant.name == "Test Sweets"
    assert merchant.type == ProviderType.LOCAL_MERCHANT
    assert merchant.provider_id is not None
    assert merchant.is_active is True

    # Retrieve merchant
    fetched = await MerchantService.get_merchant(db_session, merchant.provider_id)
    assert fetched.provider_id == merchant.provider_id
    assert fetched.name == "Test Sweets"


@pytest.mark.asyncio
async def test_list_merchants(db_session: AsyncSession) -> None:
    """Test listing all active merchants."""
    data1 = ProviderCreateSchema(
        name="Merchant A",
        type=ProviderType.LOCAL_MERCHANT,
        pincode="110001",
    )
    data2 = ProviderCreateSchema(
        name="Merchant B",
        type=ProviderType.ENTERPRISE,
        pincode="110002",
    )
    
    await MerchantService.register_merchant(db_session, data1)
    await MerchantService.register_merchant(db_session, data2)
    
    merchants = await MerchantService.list_merchants(db_session)
    assert len(merchants) >= 2
    names = [m.name for m in merchants]
    assert "Merchant A" in names
    assert "Merchant B" in names


@pytest.mark.asyncio
async def test_get_nonexistent_merchant_raises_error(db_session: AsyncSession) -> None:
    """Test retrieving a non-existent merchant raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await MerchantService.get_merchant(db_session, "non-existent-id")
