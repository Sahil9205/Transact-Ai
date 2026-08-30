from __future__ import annotations

import pytest
from app.domain.enums import ProductCategory
from app.services.intent_service import IntentService


def test_parse_english_intent_with_budget_and_deadline() -> None:
    """Test parsing English prompt with budget, time, and category."""
    prompt = "I want 1kg rasgulla under ₹500 by 6:30 PM in 110001"
    intent = IntentService.parse_intent(prompt)

    assert "rasgulla" in intent.product_query.lower()
    assert intent.max_price == 50000  # ₹500 = 50000 paise
    assert intent.deadline == "6:30 PM"
    assert intent.category == ProductCategory.SWEETS
    assert intent.pincode == "110001"


def test_parse_hinglish_intent() -> None:
    """Test parsing Hinglish prompt with colloquial phrasing."""
    prompt = "bhai 2 samosa aur sweet lassi mangwa do 300 ke andar Connaught Place mein"
    intent = IntentService.parse_intent(prompt)

    assert "samosa" in intent.product_query.lower() or "sweet lassi" in intent.product_query.lower()
    assert intent.max_price == 30000  # 300 rupees = 30000 paise
    assert intent.pincode == "110001"  # Connaught Place mapped to 110001


def test_parse_hindi_time_expression() -> None:
    """Test parsing Hindi time format (shaam 7 baje tak)."""
    prompt = "kaju katli chahiye 800 rupees max shaam 7 baje tak"
    intent = IntentService.parse_intent(prompt)

    assert "kaju katli" in intent.product_query.lower()
    assert intent.max_price == 80000
    assert intent.deadline == "19:00"
    assert intent.category == ProductCategory.SWEETS


def test_parse_intent_without_budget() -> None:
    """Test prompt without explicit budget ceiling."""
    prompt = "fresh gulab jamun in Chandni Chowk"
    intent = IntentService.parse_intent(prompt)

    assert "gulab jamun" in intent.product_query.lower()
    assert intent.max_price is None
    assert intent.category == ProductCategory.SWEETS
    assert intent.pincode == "110006"  # Chandni Chowk mapped to 110006
