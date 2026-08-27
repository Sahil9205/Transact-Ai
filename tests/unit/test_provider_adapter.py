from __future__ import annotations
import pytest
from datetime import datetime, timezone, timedelta
from app.providers.local.adapter import LocalMerchantAdapter
from app.db.models import MerchantModel, ProductModel
from app.domain.enums import ProviderType, ProductCategory, AvailabilityStatus, FreshnessTier, FulfillmentType
from app.core.exceptions import NotFoundError

pytestmark = pytest.mark.asyncio

async def setup_test_data(session):
    merchant = MerchantModel(name="AdapterMerch", type=ProviderType.LOCAL_MERCHANT.value)
    session.add(merchant)
    await session.flush()
    
    product = ProductModel(
        merchant_id=merchant.merchant_id,
        name="AdapterProd",
        category=ProductCategory.FOOD.value,
        price_amount=200,
        quantity=10,
        availability_status=AvailabilityStatus.IN_STOCK.value,
        fulfillment_type=FulfillmentType.PICKUP.value
    )
    session.add(product)
    await session.flush()
    
    return merchant, product

async def test_local_merchant_adapter_get_provider_info(db_session):
    merchant, _ = await setup_test_data(db_session)
    adapter = LocalMerchantAdapter(merchant.merchant_id, db_session)
    
    info = await adapter.get_provider_info()
    assert info.name == "AdapterMerch"
    assert info.type == ProviderType.LOCAL_MERCHANT
    
    with pytest.raises(NotFoundError):
        bad_adapter = LocalMerchantAdapter("nonexistent", db_session)
        await bad_adapter.get_provider_info()

async def test_local_merchant_adapter_search_products(db_session):
    merchant, product = await setup_test_data(db_session)
    adapter = LocalMerchantAdapter(merchant.merchant_id, db_session)
    
    results = await adapter.search_products(query="Adapter")
    assert len(results) == 1
    assert results[0].product_id == product.product_id

async def test_local_merchant_adapter_get_product(db_session):
    merchant, product = await setup_test_data(db_session)
    adapter = LocalMerchantAdapter(merchant.merchant_id, db_session)
    
    res = await adapter.get_product(product.product_id)
    assert res is not None
    assert res.name == "AdapterProd"
    
    none_res = await adapter.get_product("nonexistent")
    assert none_res is None

async def test_local_merchant_adapter_get_current_price(db_session):
    merchant, product = await setup_test_data(db_session)
    adapter = LocalMerchantAdapter(merchant.merchant_id, db_session)
    
    price = await adapter.get_current_price(product.product_id)
    assert price.amount == 200
    
    with pytest.raises(NotFoundError):
        await adapter.get_current_price("nonexistent")

async def test_local_merchant_adapter_check_availability(db_session):
    merchant, product = await setup_test_data(db_session)
    adapter = LocalMerchantAdapter(merchant.merchant_id, db_session)
    
    avail = await adapter.check_availability(product.product_id)
    assert avail.status == AvailabilityStatus.IN_STOCK
    assert avail.quantity == 10
    
    with pytest.raises(NotFoundError):
        await adapter.check_availability("nonexistent")

async def test_local_merchant_adapter_compute_freshness(db_session):
    adapter = LocalMerchantAdapter("dummy", db_session)
    
    now = datetime.now(timezone.utc)
    assert adapter._compute_freshness(now) == FreshnessTier.FRESH
    assert adapter._compute_freshness(now - timedelta(hours=3)) == FreshnessTier.STALE_WARNING
    assert adapter._compute_freshness(now - timedelta(hours=7)) == FreshnessTier.STALE
