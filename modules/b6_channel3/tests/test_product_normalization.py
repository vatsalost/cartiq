"""Tests for ProductNormalizer."""

import pytest
from modules.b6_channel3.exceptions import Channel3ValidationError
from modules.b6_channel3.normalizers.product_normalizer import ProductNormalizer


def test_product_normalizer_valid_payload():
    """Test full parsing of canonical product attributes."""
    raw = {
        "id": "item_999",
        "title": "Smart Air Purifier",
        "brands": [{"name": "AeroPure", "id": "b_1"}],
        "category": {"title": "Appliances", "slug": "appliances"},
        "description": "HEPA air purifier for home.",
        "images": [
            "https://cdn.example.com/pure1.jpg",
            {"url": "https://cdn.example.com/pure2.jpg", "is_primary": False},
        ],
        "gender": "unisex",
        "materials": ["Plastic", "Carbon"],
        "key_features": ["Quiet operation", "App controlled"],
        "unknown_extra_provider_field": 12345,  # Should be safely ignored
        "offers": [
            {
                "domain": "target.com",
                "url": "https://target.com/p/999",
                "price": 89.99,
                "currency": "USD",
                "availability": "InStock",
            }
        ],
    }

    product = ProductNormalizer.normalize_product(raw)
    assert product.product_id == "item_999"
    assert product.title == "Smart Air Purifier"
    assert product.brand == "AeroPure"
    assert product.category == "Appliances"
    assert len(product.images) == 2
    assert "https://cdn.example.com/pure1.jpg" in product.images
    assert "https://cdn.example.com/pure2.jpg" in product.images
    assert product.attributes["gender"] == "unisex"
    assert product.attributes["materials"] == ["Plastic", "Carbon"]
    assert len(product.offers) == 1


def test_product_normalizer_missing_id():
    """Test missing or empty ID raises Channel3ValidationError."""
    with pytest.raises(Channel3ValidationError):
        ProductNormalizer.normalize_product({"title": "No ID Item", "offers": []})


def test_product_normalizer_missing_title():
    """Test missing title raises Channel3ValidationError."""
    with pytest.raises(Channel3ValidationError):
        ProductNormalizer.normalize_product({"id": "valid_id", "title": "", "offers": []})


def test_product_normalizer_nested_envelope():
    """Test response wrapped in {'product': {...}} is unwrapped properly."""
    envelope = {
        "product": {
            "id": "env_1",
            "title": "Enveloped Lamp",
            "offers": [],
        }
    }
    p = ProductNormalizer.normalize_product(envelope)
    assert p.product_id == "env_1"
    assert p.title == "Enveloped Lamp"
