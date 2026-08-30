from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_lifecycle_api(client: AsyncClient) -> None:
    """Test full product lifecycle: create merchant -> add product -> get -> update -> search."""
    # 1. Register merchant
    merchant_res = await client.post(
        "/api/v1/merchants/",
        json={
            "name": "Bikanervala",
            "type": "local_merchant",
            "pincode": "110001",
        },
    )
    assert merchant_res.status_code == 201
    merchant_id = merchant_res.json()["provider_id"]

    # 2. Add product
    prod_res = await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Special Dhokla",
            "description": "Steamed savory chickpea cake",
            "category": "food",
            "price_amount": 15000,  # ₹150
            "price_currency": "INR",
            "quantity": 30,
            "availability_status": "in_stock",
            "fulfillment_type": "pickup",
            "prep_time_minutes": 10,
            "pincode": "110001",
        },
    )
    assert prod_res.status_code == 201
    prod_data = prod_res.json()
    product_id = prod_data["product_id"]
    assert prod_data["name"] == "Special Dhokla"
    assert prod_data["pricing"]["amount"] == 15000

    # 3. List merchant products
    list_res = await client.get(f"/api/v1/merchants/{merchant_id}/products")
    assert list_res.status_code == 200
    prods = list_res.json()
    assert any(p["product_id"] == product_id for p in prods)

    # 4. Get product by ID
    get_res = await client.get(f"/api/v1/products/{product_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Special Dhokla"

    # 5. Patch product (update price to ₹180 and quantity to 20)
    patch_res = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"price_amount": 18000, "quantity": 20},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["pricing"]["amount"] == 18000
    assert patch_res.json()["availability"]["quantity"] == 20

    # 6. Search products by query term
    search_res = await client.get("/api/v1/products/search?q=Dhokla")
    assert search_res.status_code == 200
    search_results = search_res.json()
    assert len(search_results) >= 1
    assert any(p["product_id"] == product_id for p in search_results)
