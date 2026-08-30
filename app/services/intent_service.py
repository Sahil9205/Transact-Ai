from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger
from app.domain.enums import ProductCategory
from app.domain.schemas import BuyerIntentSchema

logger = get_logger(__name__)

# Known pincode aliases
LOCATION_PINCODE_MAP: dict[str, str] = {
    "cp": "110001",
    "connaught place": "110001",
    "central delhi": "110001",
    "karol bagh": "110005",
    "chandni chowk": "110006",
    "green park": "110016",
    "noida": "201301",
}

# Category keyword triggers
CATEGORY_KEYWORDS: dict[ProductCategory, list[str]] = {
    ProductCategory.SWEETS: [
        "rasgulla", "gulab jamun", "kaju katli", "jalebi", "ladoo", "mithai",
        "meetha", "sweet", "sweets", "halwa", "barfi", "peda", "rasmalai", "rajbhog"
    ],
    ProductCategory.FOOD: [
        "samosa", "kachori", "pakora", "dhokla", "chaat", "tikki", "snack",
        "snacks", "nashta", "burger", "pizza", "chole", "bhature"
    ],
    ProductCategory.BEVERAGES: [
        "lassi", "chai", "tea", "coffee", "shake", "juice", "drink", "cold drink",
        "sharbat", "thandai", "beverage", "soda"
    ],
    ProductCategory.GROCERIES: [
        "atta", "rice", "dal", "sugar", "oil", "milk", "dahi", "curd", "paneer",
        "ghee", "butter", "grocery", "groceries"
    ],
}

# Noise phrases to strip from query keyword extraction
NOISE_PATTERNS = [
    r"\b(i want|i need|can you get me|please order|order|bhejo|chahiye|mangwa do|le aao)\b",
    r"\b(under|below|less than|max|maximum|budget|ke andar|tak)\b",
    r"\b(by|at|before|within|tak|baje)\b",
    r"\b(urgent|fast|quickly|jaldi)\b",
    r"\b(in|near|at|around)\s+[a-zA-Z0-9\s]+",
]


class IntentService:
    """Service for parsing natural language commerce intent into validated BuyerIntentSchema."""

    @staticmethod
    def parse_intent(prompt: str) -> BuyerIntentSchema:
        """Parses an unstructured English/Hindi/Hinglish prompt into a structured BuyerIntentSchema."""
        logger.debug(f"Parsing intent from prompt: '{prompt}'")
        text = prompt.strip()
        text_lower = text.lower()

        # 1. Extract Price Ceiling (e.g. ₹500, under 500, 500 ke andar, budget 600)
        max_price_paise = IntentService._extract_price_ceiling(text_lower)

        # 2. Extract Deadline (e.g. 6:30 PM, 18:30, within 20 mins, shaam 7 baje)
        deadline = IntentService._extract_deadline(text_lower)

        # 3. Extract Pincode or Location mapping
        pincode = IntentService._extract_pincode(text_lower)

        # 4. Infer Category
        category = IntentService._infer_category(text_lower)

        # 5. Extract cleaned Product Query Keyword
        product_query = IntentService._extract_product_query(text)

        intent = BuyerIntentSchema(
            product_query=product_query,
            max_price=max_price_paise,
            currency="INR",
            deadline=deadline,
            category=category,
            pincode=pincode,
        )
        logger.info(
            "Extracted intent",
            query=intent.product_query,
            max_price=intent.max_price,
            deadline=intent.deadline,
            category=intent.category.value if intent.category else None,
            pincode=intent.pincode,
        )
        return intent

    @staticmethod
    def _extract_price_ceiling(text: str) -> int | None:
        """Extracts max budget ceiling and converts to integer paise."""
        # Pattern 1: ₹500, Rs. 500, Rs 500, INR 500
        rupee_match = re.search(r"(?:₹|rs\.?|inr)\s*(\d+(?:,\d+)*(?:\.\d+)?)", text)
        if rupee_match:
            val = float(rupee_match.group(1).replace(",", ""))
            return int(val * 100)

        # Pattern 2: under 500, below 500, 500 ke andar, budget 500, 500 max
        budget_match = re.search(
            r"(?:under|below|less than|budget|max|maximum)\s*(\d+(?:,\d+)?)|(\d+(?:,\d+)?)\s*(?:ke andar|max|tak|rupees|rs)",
            text,
        )
        if budget_match:
            num_str = budget_match.group(1) or budget_match.group(2)
            if num_str:
                val = float(num_str.replace(",", ""))
                return int(val * 100)

        return None

    @staticmethod
    def _extract_deadline(text: str) -> str | None:
        """Extracts time deadline strings (e.g. '18:30', '6:30 PM', 'within 20 mins')."""
        # Pattern 1: 18:30 or 6:30 PM / 6:30pm
        time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)|\d{1,2}:\d{2})\b", text)
        if time_match:
            return time_match.group(1).upper()

        # Pattern 2: within X mins / minutes / mins mein
        duration_match = re.search(r"(?:within|in|under)\s*(\d+)\s*(?:min|mins|minutes)", text)
        if duration_match:
            return f"within {duration_match.group(1)} mins"

        # Pattern 3: Hindi time format (shaam 7 baje, 6 baje tak)
        hindi_time = re.search(r"(\d{1,2})\s*baje", text)
        if hindi_time:
            hour = int(hindi_time.group(1))
            if "shaam" in text or "raat" in text and hour < 12:
                hour += 12
            return f"{hour:02d}:00"

        return None

    @staticmethod
    def _extract_pincode(text: str) -> str | None:
        """Extracts explicit 6-digit Indian pincode or infers from location keyword."""
        # 1. Explicit 6-digit number
        pincode_match = re.search(r"\b([1-9][0-9]{5})\b", text)
        if pincode_match:
            return pincode_match.group(1)

        # 2. Location mapping
        for loc_name, pin in LOCATION_PINCODE_MAP.items():
            if re.search(rf"\b{re.escape(loc_name)}\b", text):
                return pin

        return None

    @staticmethod
    def _infer_category(text: str) -> ProductCategory | None:
        """Infers product category based on keyword vocabulary."""
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    return cat
        return None

    @staticmethod
    def _extract_product_query(text: str) -> str:
        """Strips conversational noise and price/time metadata to isolate the product query."""
        cleaned = text

        # Strip price expressions (e.g. ₹500, under 500, 500 ke andar)
        cleaned = re.sub(r"(?:₹|rs\.?|inr)\s*\d+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?:under|below|budget|max)\s*\d+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\d+\s*(?:ke andar|rupees|rs)", "", cleaned, flags=re.IGNORECASE)

        # Strip pincodes
        cleaned = re.sub(r"\b[1-9][0-9]{5}\b", "", cleaned)

        # Strip time expressions
        cleaned = re.sub(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?:within|in)\s*\d+\s*(?:min|mins|minutes)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\d+\s*baje\s*(?:tak)?", "", cleaned, flags=re.IGNORECASE)

        # Strip common noise keywords
        for pattern in NOISE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Clean punctuation and excessive whitespace
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # If stripping took everything away, fallback to original text
        return cleaned if cleaned else text.strip()
