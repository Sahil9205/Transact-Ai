from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed import SEED_PROVIDERS, seed_database
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService


@pytest.mark.asyncio
async def test_seed_database_multi_providers(db_session: AsyncSession) -> None:
    """Test multi-provider seed catalog execution and verify seeded entities."""
    # Seed database
    await seed_database(db_session, vector_service=None)

    # 1. Verify merchants seeded
    merchants = await MerchantService.list_merchants(db_session)
    assert len(merchants) >= 5
    merchant_names = [m.name for m in merchants]
    assert any("Sharma Sweets" in n for n in merchant_names)
    assert any("Blinkit" in n for n in merchant_names)
    assert any("Zepto" in n for n in merchant_names)
    assert any("Amazon" in n for n in merchant_names)
    assert any("Apollo" in n for n in merchant_names)

    # 2. Verify products exist
    from app.db.repository import ProductRepository
    for m in merchants:
        products = await ProductRepository.search(db_session, merchant_id=m.provider_id)
        assert len(products) >= 1
