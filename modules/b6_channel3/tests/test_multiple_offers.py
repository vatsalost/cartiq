"""Tests for handling canonical products with multiple retailer offers and offer selection."""

from decimal import Decimal
import pytest
from modules.b6_channel3.constants import OfferAvailability
from modules.b6_channel3.exceptions import (
    CurrencyMismatchError,
    MandateConstraintViolationError,
    OfferNotFoundError,
    OfferUnavailableError,
)
from modules.b6_channel3.models.offer import NormalizedOffer
from modules.b6_channel3.models.product import NormalizedProduct
from modules.b6_channel3.services.offer_selection import (
    OfferSelectionService,
    SpendingMandate,
)


@pytest.fixture
def multi_offer_product() -> NormalizedProduct:
    """Fixture with three distinct retailer offers for one canonical item."""
    offers = [
        NormalizedOffer(
            offer_key="off_target_1",
            domain="target.com",
            price_amount=Decimal("49.99"),
            currency="USD",
            availability=OfferAvailability.IN_STOCK.value,
            condition="new",
            buy_url="https://buy.trychannel3.com/target/1",
        ),
        NormalizedOffer(
            offer_key="off_bestbuy_2",
            domain="bestbuy.com",
            price_amount=Decimal("45.00"),
            currency="USD",
            availability=OfferAvailability.IN_STOCK.value,
            condition="new",
            buy_url="https://buy.trychannel3.com/bestbuy/2",
        ),
        NormalizedOffer(
            offer_key="off_walmart_3",
            domain="walmart.com",
            price_amount=Decimal("42.00"),
            currency="USD",
            availability=OfferAvailability.OUT_OF_STOCK.value,
            condition="new",
            buy_url="https://buy.trychannel3.com/walmart/3",
        ),
        NormalizedOffer(
            offer_key="off_uk_seller_4",
            domain="currys.co.uk",
            price_amount=Decimal("38.00"),
            currency="GBP",
            availability=OfferAvailability.IN_STOCK.value,
            condition="new",
            buy_url="https://buy.trychannel3.com/currys/4",
        ),
    ]
    return NormalizedProduct(
        product_id="prod_multi",
        title="Smart Bluetooth Speaker",
        offers=offers,
    )


def test_multiple_offers_distinct_identities(multi_offer_product: NormalizedProduct):
    """Verify offers remain separate with distinct keys and prices."""
    assert len(multi_offer_product.offers) == 4
    keys = {o.offer_key for o in multi_offer_product.offers}
    assert len(keys) == 4
    assert multi_offer_product.get_best_price_offer("USD").offer_key == "off_bestbuy_2"


def test_select_offer_success(multi_offer_product: NormalizedProduct):
    """Test successful selection of an in-stock offer satisfying mandate."""
    mandate = SpendingMandate(
        max_budget=Decimal("100.00"),
        per_item_cap=Decimal("50.00"),
        currency="USD",
        allowed_domains=["bestbuy.com", "target.com"],
    )

    selected = OfferSelectionService.select_offer(
        product=multi_offer_product,
        offer_key="off_bestbuy_2",
        mandate=mandate,
    )
    assert selected.offer_key == "off_bestbuy_2"
    assert selected.price_amount == Decimal("45.00")
    assert selected.domain == "bestbuy.com"


def test_select_offer_not_found_raises(multi_offer_product: NormalizedProduct):
    """Test non-existent offer key raises OfferNotFoundError."""
    with pytest.raises(OfferNotFoundError):
        OfferSelectionService.select_offer(
            product=multi_offer_product,
            offer_key="non_existent_key",
        )


def test_select_unavailable_offer_raises(multi_offer_product: NormalizedProduct):
    """Test out-of-stock offer is rejected deterministically."""
    with pytest.raises(OfferUnavailableError):
        OfferSelectionService.select_offer(
            product=multi_offer_product,
            offer_key="off_walmart_3",
        )


def test_select_currency_mismatch_raises(multi_offer_product: NormalizedProduct):
    """Test foreign currency offer rejected when mandate specifies USD."""
    mandate = SpendingMandate(currency="USD")
    with pytest.raises(CurrencyMismatchError):
        OfferSelectionService.select_offer(
            product=multi_offer_product,
            offer_key="off_uk_seller_4",
            mandate=mandate,
        )


def test_select_offer_exceeds_per_item_cap(multi_offer_product: NormalizedProduct):
    """Test offer rejected when price exceeds per-item cap."""
    mandate = SpendingMandate(per_item_cap=Decimal("40.00"), currency="USD")
    with pytest.raises(MandateConstraintViolationError, match="exceeds per-item cap"):
        OfferSelectionService.select_offer(
            product=multi_offer_product,
            offer_key="off_target_1",
            mandate=mandate,
        )


def test_select_offer_violates_domain_whitelist(multi_offer_product: NormalizedProduct):
    """Test offer rejected when domain not in allowed whitelist."""
    mandate = SpendingMandate(allowed_domains=["walmart.com", "amazon.com"])
    with pytest.raises(MandateConstraintViolationError, match="not in allowed domain whitelist"):
        OfferSelectionService.select_offer(
            product=multi_offer_product,
            offer_key="off_target_1",
            mandate=mandate,
        )


def test_select_offer_violates_domain_blacklist(multi_offer_product: NormalizedProduct):
    """Test offer rejected when domain is blacklisted."""
    mandate = SpendingMandate(blocked_domains=["target.com"])
    with pytest.raises(MandateConstraintViolationError, match="prohibited by domain blacklist"):
        OfferSelectionService.select_offer(
            product=multi_offer_product,
            offer_key="off_target_1",
            mandate=mandate,
        )
