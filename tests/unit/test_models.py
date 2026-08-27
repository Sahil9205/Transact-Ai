from __future__ import annotations
import pytest
from app.db.models import MerchantModel, ProductModel
from app.domain.enums import ProviderType, ProductCategory

pytestmark = pytest.mark.asyncio

async def test_merchant_model_uuid(db_session):
    merchant = MerchantModel(name="Test", type=ProviderType.LOCAL_MERCHANT.value)
    db_session.add(merchant)
    await db_session.flush()
    assert merchant.id is not None
    assert merchant.merchant_id is not None
    assert isinstance(merchant.merchant_id, str)
    assert len(merchant.merchant_id) > 10

async def test_product_model_instantiation(db_session):
    merchant = MerchantModel(name="Test", type=ProviderType.LOCAL_MERCHANT.value)
    db_session.add(merchant)
    await db_session.flush()
    
    product = ProductModel(
        merchant_id=merchant.merchant_id,
        name="Prod",
        category=ProductCategory.FOOD.value,
        price_amount=100
    )
    db_session.add(product)
    await db_session.flush()
    assert product.id is not None
    assert product.product_id is not None

async def test_tables_created(db_session):
    # Simply using the db_session implies tables are created since we can insert
    merchant = MerchantModel(name="Test2", type=ProviderType.ENTERPRISE.value)
    db_session.add(merchant)
    await db_session.flush()
    assert merchant.id is not None
