from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_get_merchant_api(client: AsyncClient) -> None:
    """Test POST /api/v1/merchants/ and GET /api/v1/merchants/{id}."""
    payload = {
        "name": "Aggarwal Sweets",
        "type": "local_merchant",
        "description": "Authentic North Indian Sweets",
        "location": "Karol Bagh, Delhi",
        "pincode": "110005",
    }
    
    # 1. Register merchant
    response = await client.post("/api/v1/merchants/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aggarwal Sweets"
    assert data["type"] == "local_merchant"
    assert "provider_id" in data
    merchant_id = data["provider_id"]

    # 2. Get merchant by ID
    get_res = await client.get(f"/api/v1/merchants/{merchant_id}")
    assert get_res.status_code == 200
    assert get_res.json()["provider_id"] == merchant_id
    assert get_res.json()["name"] == "Aggarwal Sweets"


@pytest.mark.asyncio
async def test_list_merchants_api(client: AsyncClient) -> None:
    """Test GET /api/v1/merchants/."""
    response = await client.get("/api/v1/merchants/")
    assert response.status_code == 200
    merchants = response.json()
    assert isinstance(merchants, list)
    # Seed merchants or newly registered should be present
    assert len(merchants) >= 1


@pytest.mark.asyncio
async def test_get_nonexistent_merchant_api(client: AsyncClient) -> None:
    """Test GET /api/v1/merchants/{id} with invalid ID."""
    response = await client.get("/api/v1/merchants/non-existent-id")
    assert response.status_code in (400, 404)
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_and_activate_merchant_api(client: AsyncClient) -> None:
    """Test PATCH /api/v1/merchants/{id} and POST /api/v1/merchants/{id}/activate."""
    # 1. Register a merchant with contact details
    payload = {
        "name": "Haldiram CP Store",
        "type": "enterprise",
        "description": "Quick sweet outlet",
        "location": "Connaught Place, Delhi",
        "pincode": "110001",
        "contact_email": "cp@haldiram.com",
        "contact_phone": "9811122233",
        "business_type": "sweet_shop",
    }
    create_res = await client.post("/api/v1/merchants/", json=payload)
    assert create_res.status_code == 201
    m_data = create_res.json()
    m_id = m_data["provider_id"]
    assert m_data.get("api_key") is not None
    assert m_data.get("contact_email") == "cp@haldiram.com"

    # 2. Update merchant profile via PATCH
    patch_res = await client.patch(
        f"/api/v1/merchants/{m_id}",
        json={"location": "Odeon Building, Connaught Place", "business_type": "restaurant"},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["location"] == "Odeon Building, Connaught Place"
    assert updated_data["business_type"] == "restaurant"

    # 3. Activate merchant
    act_res = await client.post(f"/api/v1/merchants/{m_id}/activate")
    assert act_res.status_code == 200
    assert act_res.json()["onboarding_status"] == "active"


@pytest.mark.asyncio
async def test_merchant_dashboard_stats_and_portal_pages(client: AsyncClient) -> None:
    """Test dashboard stats endpoint and HTML rendering for /merchant/register and /merchant/dashboard."""
    # 1. Register store
    payload = {
        "name": "Bikanervala Regal",
        "type": "local_merchant",
        "location": "Regal Building, CP",
        "pincode": "110001",
    }
    m_res = await client.post("/api/v1/merchants/", json=payload)
    assert m_res.status_code == 201
    m_id = m_res.json()["provider_id"]

    # 2. Add a product to the merchant
    p_payload = {
        "name": "Motichoor Ladoo (500g)",
        "category": "sweets",
        "price_amount": 32000,
        "price_currency": "INR",
        "quantity": 25,
        "prep_time_minutes": 10,
        "pincode": "110001",
    }
    p_res = await client.post(f"/api/v1/merchants/{m_id}/products", json=p_payload)
    assert p_res.status_code == 201

    # 3. Verify JSON dashboard stats
    stats_res = await client.get(f"/api/v1/merchants/{m_id}/dashboard-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_products"] >= 1
    assert "platform_breakdown" in stats

    # 4. Test HTML Registration Page
    reg_page_res = await client.get("/merchant/register")
    assert reg_page_res.status_code == 200
    assert "text/html" in reg_page_res.headers.get("content-type", "")
    assert "Onboarding" in reg_page_res.text

    # 5. Test HTML Dashboard Page
    dash_page_res = await client.get(f"/merchant/dashboard/{m_id}")
    assert dash_page_res.status_code == 200
    assert "text/html" in dash_page_res.headers.get("content-type", "")
    assert "Bikanervala Regal" in dash_page_res.text
    assert "Live Incoming Orders" in dash_page_res.text or "Live Orders" in dash_page_res.text

    # 6. Test Merchant Choice Landing Page (/ and /merchant)
    landing_res = await client.get("/merchant")
    assert landing_res.status_code == 200
    assert "text/html" in landing_res.headers.get("content-type", "")
    assert "I am an Existing Store Partner" in landing_res.text
    assert "I am a New Store Partner" in landing_res.text


@pytest.mark.asyncio
async def test_flexible_pricing_and_status_toggles(client: AsyncClient) -> None:
    """Test weight-based pricing, store operational status toggle, and product availability toggle."""
    # 1. Register a merchant
    m_res = await client.post(
        "/api/v1/merchants/",
        json={
            "name": "Bikanervala Sweets Karol Bagh",
            "type": "local_merchant",
            "location": "Ajmal Khan Road, Karol Bagh",
            "pincode": "110005",
        },
    )
    assert m_res.status_code == 201
    m_id = m_res.json()["provider_id"]

    # 2. Toggle Store Operational Status to 'paused'
    pause_res = await client.post(
        f"/api/v1/merchants/{m_id}/status",
        json={"operational_status": "paused"},
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["operational_status"] == "paused"

    # Re-open store
    open_res = await client.post(
        f"/api/v1/merchants/{m_id}/status",
        json={"operational_status": "open"},
    )
    assert open_res.status_code == 200
    assert open_res.json()["operational_status"] == "open"

    # 3. Add a weight-based product (e.g. ₹220/kg, min 250g, step 250g)
    prod_payload = {
        "name": "Kaju Katli Special",
        "category": "sweets",
        "price_amount": 22000,
        "price_currency": "INR",
        "pricing_type": "weight_based",
        "unit": "kg",
        "min_quantity": 0.25,
        "increment_step": 0.25,
        "quantity": 15,
        "prep_time_minutes": 10,
        "pincode": "110005",
        "availability_status": "in_stock",
    }
    p_res = await client.post(f"/merchants/{m_id}/products", json=prod_payload)
    assert p_res.status_code == 201
    p_data = p_res.json()
    assert p_data["pricing"]["pricing_type"] == "weight_based"
    assert p_data["pricing"]["unit"] == "kg"
    assert p_data["pricing"]["min_quantity"] == 0.25
    assert p_data["pricing"]["increment_step"] == 0.25
    prod_id = p_data["product_id"]

    # 4. Toggle Product Availability to 'out_of_stock'
    avail_res = await client.post(
        f"/api/v1/merchants/{m_id}/products/{prod_id}/availability",
        json={"availability_status": "out_of_stock"},
    )
    assert avail_res.status_code == 200
    assert avail_res.json()["availability_status"] == "out_of_stock"

    # 5. Check dashboard stats returns the product with flexible pricing
    stats_res = await client.get(f"/api/v1/merchants/{m_id}/dashboard-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert len(stats["products"]) >= 1
    found = next((p for p in stats["products"] if p["product_id"] == prod_id), None)
    assert found is not None
    assert found["pricing_type"] == "weight_based"
    assert found["unit"] == "kg"
    assert found["min_quantity"] == 0.25
    assert found["availability_status"] == "out_of_stock"

