from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_recovery_api_endpoints(client: AsyncClient) -> None:
    """Test REST API endpoints for failure diagnosis and smart alternatives."""
    # 1. Test POST /api/v1/recovery/diagnose
    diag_res = await client.post(
        "/api/v1/recovery/diagnose",
        json={
            "status": "no_candidates",
            "error_details": ["Stock level is 0"],
            "product_name": "Kaju Barfi",
        },
    )
    assert diag_res.status_code == 200
    diag_data = diag_res.json()
    assert diag_data["failure_code"] == "OUT_OF_STOCK"
    assert "remediation_strategy" in diag_data

    # 2. Onboard merchant & product
    m_res = await client.post(
        "/api/v1/merchants/",
        json={"name": "Zepto Delhi Hub", "type": "enterprise", "pincode": "110001"},
    )
    assert m_res.status_code == 201
    merchant_id = m_res.json()["provider_id"]

    await client.post(
        f"/api/v1/merchants/{merchant_id}/products",
        json={
            "name": "Haldiram Rasgulla",
            "category": "sweets",
            "price_amount": 34000,  # ₹340
            "quantity": 10,
            "availability_status": "in_stock",
            "pincode": "110001",
        },
    )

    # 3. Test POST /api/v1/recovery/alternatives
    alts_res = await client.post(
        "/api/v1/recovery/alternatives",
        json={
            "product_query": "Rasgulla",
            "max_price_inr": 300.0,
            "pincode": "110001",
            "limit": 3,
        },
    )
    assert alts_res.status_code == 200
    alts_data = alts_res.json()
    assert len(alts_data) >= 1
    assert alts_data[0]["merchant_name"] == "Zepto Delhi Hub"
    assert alts_data[0]["relaxation_type"] == "price_headroom"
