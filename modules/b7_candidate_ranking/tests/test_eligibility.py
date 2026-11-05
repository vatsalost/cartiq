"""Tests for EligibilityFilter pre-filtering logic."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from modules.b7_candidate_ranking.config import RankingConfig
from modules.b7_candidate_ranking.eligibility import EligibilityFilter
from modules.b7_candidate_ranking.models import (
    MandateSnapshot,
    RejectionCode,
    ShoppingRequest,
)
from modules.b7_candidate_ranking.tests.conftest import make_candidate_option


def test_valid_candidate_passes_eligibility(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test fully compliant candidate passes with zero rejection reasons."""
    candidate = make_candidate_option(
        price=Decimal("35.00"),
        availability="InStock",
        condition="new",
        currency="USD",
    )
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)
    assert rejections == []


def test_out_of_stock_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test out-of-stock offer is rejected with OUT_OF_STOCK."""
    candidate = make_candidate_option(availability="OutOfStock")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.OUT_OF_STOCK in codes


def test_unknown_availability_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test unknown availability is rejected and not assumed in-stock."""
    candidate = make_candidate_option(availability="Unknown")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.OUT_OF_STOCK in codes


def test_wrong_currency_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test foreign currency offer rejected with WRONG_CURRENCY."""
    candidate = make_candidate_option(currency="EUR")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.WRONG_CURRENCY in codes


def test_exceeding_request_price_limit(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test price above user's max_price is rejected."""
    # max_price is 45.00, set price to 48.00
    candidate = make_candidate_option(price=Decimal("48.00"))
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.ABOVE_REQUEST_PRICE_LIMIT in codes


def test_exceeding_mandate_per_item_cap(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test price exceeding mandate per_item_cap is rejected."""
    # mandate per_item_cap is 50.00, user max_price is 100.00
    req = default_request.model_copy(update={"max_price": Decimal("100.00")})
    candidate = make_candidate_option(price=Decimal("55.00"))
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, req, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.ABOVE_PER_ITEM_CAP in codes


def test_blocked_category_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test product in mandate's blocked categories is rejected."""
    candidate = make_candidate_option(category="Hazardous Materials")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.BLOCKED_CATEGORY in codes


def test_category_not_in_allowed_categories(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test product category not in allowed categories list is rejected."""
    candidate = make_candidate_option(category="Automotive Accessories")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.CATEGORY_NOT_ALLOWED in codes


def test_retailer_outside_allowlist_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test merchant outside allowed retailers is rejected."""
    candidate = make_candidate_option(domain="unapproved-merchant.com")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.RETAILER_NOT_ALLOWED in codes


def test_wrong_condition_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test refurbished item rejected when new is required."""
    candidate = make_candidate_option(condition="refurbished")
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.WRONG_CONDITION in codes


def test_missing_required_attribute_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test product lacking requested required attribute is rejected."""
    # request requires 'dimmable': 'true' and 'type': 'desk'
    candidate = make_candidate_option(attributes={"type": "floor"})  # missing dimmable and wrong type
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.MISSING_REQUIRED_ATTRIBUTE in codes


def test_stale_offer_data_rejected(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test offer with old timestamp is rejected for staleness."""
    stale_time = datetime.now(timezone.utc) - timedelta(days=2)
    candidate = make_candidate_option(observed_at=stale_time)
    filter_svc = EligibilityFilter(config=RankingConfig(max_data_age_seconds=86400))
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = [r.code for r in rejections]
    assert RejectionCode.STALE_PRODUCT_DATA in codes


def test_multiple_rejection_reasons_preserved(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Verify that multiple simultaneous violations are all captured."""
    candidate = make_candidate_option(
        price=Decimal("80.00"),  # Exceeds request limit and mandate cap
        currency="EUR",          # Wrong currency
        availability="OutOfStock",  # Out of stock
        domain="shady-site.com",  # Unapproved retailer
    )
    filter_svc = EligibilityFilter()
    rejections = filter_svc.evaluate(candidate, default_request, default_mandate)

    codes = {r.code for r in rejections}
    assert RejectionCode.ABOVE_REQUEST_PRICE_LIMIT in codes
    assert RejectionCode.ABOVE_PER_ITEM_CAP in codes
    assert RejectionCode.WRONG_CURRENCY in codes
    assert RejectionCode.OUT_OF_STOCK in codes
    assert RejectionCode.RETAILER_NOT_ALLOWED in codes
