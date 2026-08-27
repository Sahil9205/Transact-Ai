from __future__ import annotations
import pytest
from app.db.repository import MerchantRepository, ProductRepository, AuditRepository
from app.domain.schemas import ProviderCreateSchema, ProductCreateSchema, ProductUpdateSchema
from app.domain.enums import ProviderType, ProductCategory, AvailabilityStatus, FulfillmentType, AuditEventType
from app.core.exceptions import NotFoundError

pytestmark = pytest.mark.asyncio

async def test_merchant_repository_create_and_get(db_session):
    data = ProviderCreateSchema(name="Merch", type=ProviderType.LOCAL_MERCHANT, pincode="123")
    merchant = await MerchantRepository.create(db_session, data)
    assert merchant.name == "Merch"
    
    fetched = await MerchantRepository.get_by_merchant_id(db_session, merchant.merchant_id)
    assert fetched.id == merchant.id
    
    with pytest.raises(NotFoundError):
        await MerchantRepository.get_by_merchant_id(db_session, "nonexistent")

async def test_merchant_repository_list_active(db_session):
    data1 = ProviderCreateSchema(name="Merch1", type=ProviderType.LOCAL_MERCHANT)
    await MerchantRepository.create(db_session, data1)
    
    data2 = ProviderCreateSchema(name="Merch2", type=ProviderType.LOCAL_MERCHANT)
    merch2 = await MerchantRepository.create(db_session, data2)
    merch2.is_active = False
    await db_session.flush()
    
    active = await MerchantRepository.list_active(db_session)
    assert len(active) >= 1
    assert "Merch1" in [m.name for m in active]
    assert "Merch2" not in [m.name for m in active]

async def test_product_repository_create_and_get(db_session):
    data = ProviderCreateSchema(name="Merch", type=ProviderType.LOCAL_MERCHANT)
    merchant = await MerchantRepository.create(db_session, data)
    
    pdata = ProductCreateSchema(name="Prod", category=ProductCategory.FOOD, price_amount=100, quantity=5)
    product = await ProductRepository.create(db_session, merchant.merchant_id, pdata)
    assert product.name == "Prod"
    
    fetched = await ProductRepository.get_by_product_id(db_session, product.product_id)
    assert fetched.id == product.id
    
    with pytest.raises(NotFoundError):
        await ProductRepository.get_by_product_id(db_session, "nonexistent")

async def test_product_repository_search(db_session):
    data = ProviderCreateSchema(name="Merch", type=ProviderType.LOCAL_MERCHANT)
    merchant = await MerchantRepository.create(db_session, data)
    
    await ProductRepository.create(db_session, merchant.merchant_id, ProductCreateSchema(name="Apple", category=ProductCategory.FOOD, price_amount=100, quantity=5, pincode="123"))
    await ProductRepository.create(db_session, merchant.merchant_id, ProductCreateSchema(name="Banana", category=ProductCategory.FOOD, price_amount=50, quantity=5, pincode="123"))
    await ProductRepository.create(db_session, merchant.merchant_id, ProductCreateSchema(name="Milk", category=ProductCategory.BEVERAGES, price_amount=60, quantity=5, pincode="456"))
    
    # Query filter
    res = await ProductRepository.search(db_session, query="app")
    assert len(res) == 1
    assert res[0].name == "Apple"
    
    # Category filter
    res = await ProductRepository.search(db_session, category=ProductCategory.BEVERAGES.value)
    assert len(res) == 1
    assert res[0].name == "Milk"

async def test_product_repository_update(db_session):
    m_data = ProviderCreateSchema(name="Merch", type=ProviderType.LOCAL_MERCHANT)
    merchant = await MerchantRepository.create(db_session, m_data)
    
    p_data = ProductCreateSchema(name="Prod", category=ProductCategory.FOOD, price_amount=100, quantity=5)
    product = await ProductRepository.create(db_session, merchant.merchant_id, p_data)
    
    update_data = ProductUpdateSchema(price_amount=150, availability_status=AvailabilityStatus.OUT_OF_STOCK)
    updated = await ProductRepository.update(db_session, product.product_id, update_data)
    assert updated.price_amount == 150
    assert updated.availability_status == AvailabilityStatus.OUT_OF_STOCK.value

async def test_audit_repository_log_event(db_session):
    event = await AuditRepository.log_event(db_session, event_type=AuditEventType.INTENT_RECEIVED.value, metadata={"test": "data"})
    assert event.id is not None
    assert event.event_type == AuditEventType.INTENT_RECEIVED.value
    assert event.metadata_json == {"test": "data"}
