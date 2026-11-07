"""Tests for OfferNormalizer."""

from decimal import Decimal
import pytest
from server.app.services.discovery.constants import OfferAvailability, OfferCondition
from server.app.services.discovery.exceptions import Channel3ValidationError
from server.app.services.discovery.normalizers.offer_normalizer import OfferNormalizer


def test_offer_normalization_valid():
    """Test full parsing of single retailer offer."""
    raw = {
        "domain": "https://www.bestbuy.com/site/item/123",
        "merchant_name": "Best Buy",
        "url": "https://buy.trychannel3.com/bestbuy/123?tracking=xyz",
        "price": {
            "price": "99.95",
            "currency": "usd",
            "compare_at_price": "129.99",
        },
        "availability": "InStock",
        "condition": "new",
        "commission_rate": "0.04",
    }

    offer = OfferNormalizer.normalize_offer(raw)
    assert offer.domain == "bestbuy.com"
    assert offer.price_amount == Decimal("99.95")
    assert isinstance(offer.price_amount, Decimal)
    assert offer.currency == "USD"
    assert offer.compare_at_price == Decimal("129.99")
    assert offer.commission_rate == Decimal("0.04")
    assert offer.availability == OfferAvailability.IN_STOCK.value
    assert offer.condition == OfferCondition.NEW.value
    assert offer.buy_url == "https://buy.trychannel3.com/bestbuy/123?tracking=xyz"
    assert offer.offer_key.startswith("off_")


def test_stable_offer_key_immutable_to_price_changes():
    """Verify offer key does not change when price or availability fluctuates."""
    raw_v1 = {
        "domain": "target.com",
        "merchant_id": "tgt_1",
        "url": "https://buy.trychannel3.com/target/itemA?v=1",
        "price": 50.00,
        "currency": "USD",
        "availability": "InStock",
    }
    raw_v2 = {
        "domain": "target.com",
        "merchant_id": "tgt_1",
        "url": "https://buy.trychannel3.com/target/itemA?v=2",  # query params stripped
        "price": 75.00,  # Price increased
        "availability": "OutOfStock",
    }

    key1 = OfferNormalizer.generate_offer_key(raw_v1)
    key2 = OfferNormalizer.generate_offer_key(raw_v2)
    assert key1 == key2


def test_offer_normalizer_missing_price():
    """Test offer with missing price raises Channel3ValidationError."""
    raw = {
        "domain": "store.com",
        "url": "https://store.com/item",
        "currency": "USD",
        "availability": "InStock",
    }
    with pytest.raises(Channel3ValidationError, match="Offer price cannot be None"):
        OfferNormalizer.normalize_offer(raw)


def test_offer_normalizer_invalid_price():
    """Test offer with non-numeric price string raises Channel3ValidationError."""
    raw = {
        "domain": "store.com",
        "url": "https://store.com/item",
        "price": "N/A",
        "currency": "USD",
    }
    with pytest.raises(Channel3ValidationError, match="Invalid price amount"):
        OfferNormalizer.normalize_offer(raw)


def test_offer_normalizer_negative_price():
    """Test offer with negative price raises Channel3ValidationError."""
    raw = {
        "domain": "store.com",
        "url": "https://store.com/item",
        "price": -10.0,
        "currency": "USD",
    }
    with pytest.raises(Channel3ValidationError, match="Price cannot be negative"):
        OfferNormalizer.normalize_offer(raw)


def test_offer_normalizer_missing_currency():
    """Test offer with missing currency raises Channel3ValidationError."""
    raw = {
        "domain": "store.com",
        "url": "https://store.com/item",
        "price": 25.0,
        "currency": None,
    }
    with pytest.raises(Channel3ValidationError, match="Invalid currency code"):
        OfferNormalizer.normalize_offer(raw)


def test_offer_normalizer_unknown_availability_and_condition():
    """Test unmapped availability/condition falls back to 'Unknown'."""
    raw = {
        "domain": "store.com",
        "url": "https://store.com/item",
        "price": 25.0,
        "currency": "USD",
        "availability": "custom_warehouse_pending",
        "condition": "unspecified",
    }
    offer = OfferNormalizer.normalize_offer(raw)
    assert offer.availability == OfferAvailability.UNKNOWN.value
    assert offer.condition == OfferCondition.UNKNOWN.value
