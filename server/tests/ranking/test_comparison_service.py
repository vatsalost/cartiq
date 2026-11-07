"""Tests for ComparisonService end-to-end integration and B6 adapter."""

from decimal import Decimal
import pytest
from server.app.services.ranking.comparison_service import ComparisonService
from server.app.services.ranking.models import (
    ComparisonResult,
    EligibilityStatus,
    MandateSnapshot,
    ShoppingRequest,
)
from server.tests.ranking.conftest import make_candidate_option


def test_end_to_end_comparison_pipeline(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test full comparison lifecycle: filtering, ranking, top selection, and explanation."""
    c1 = make_candidate_option(product_id="lamp_1", price=Decimal("32.00"), brand="Lumina")
    c2 = make_candidate_option(product_id="lamp_2", price=Decimal("38.00"), brand="OtherBrand")
    c3_oos = make_candidate_option(product_id="lamp_3", price=Decimal("20.00"), availability="OutOfStock")

    svc = ComparisonService()
    result = svc.compare_and_rank(
        request=default_request,
        candidates=[c1, c2, c3_oos],
        mandate=default_mandate,
    )

    assert isinstance(result, ComparisonResult)
    assert len(result.ranked_candidates) == 2
    assert len(result.rejected_candidates) == 1
    assert result.selected_candidate is not None
    assert result.selected_candidate.product_id == "lamp_1"
    assert result.selected_candidate.ranking_position == 1
    assert "lamp_1" in result.explanation or "Lumina Touch Desk Lamp" in result.explanation
    assert result.evaluation_timestamp is not None


def test_adapt_b6_product_compatibility():
    """Verify B6 NormalizedProduct compatibility through the isolated B7 adapter."""
    # Mocking B6 structure or using real B6 models
    class MockB6Offer:
        offer_key = "off_mock_1"
        domain = "target.com"
        buy_url = "https://buy.example.com"
        price_amount = Decimal("39.99")
        currency = "USD"
        availability = "InStock"
        condition = "new"

    class MockB6Product:
        product_id = "prod_b6_100"
        title = "B6 Desk Lamp"
        brand = "Lumina"
        category = "Home Lighting"
        description = "Adapted from B6 normalization"
        attributes = {"type": "desk", "dimmable": "true"}
        variants = []
        image_url = "https://cdn.example.com/img.jpg"
        offers = [MockB6Offer()]

    options = ComparisonService.adapt_b6_product(MockB6Product())
    assert len(options) == 1
    assert options[0].candidate_id == "prod_b6_100:off_mock_1"
    assert options[0].product.product_id == "prod_b6_100"
    assert options[0].offer.price_amount == Decimal("39.99")


def test_empty_candidate_pool(default_request: ShoppingRequest):
    """Test behavior when candidate list is empty."""
    svc = ComparisonService()
    result = svc.compare_and_rank(request=default_request, candidates=[])

    assert result.ranked_candidates == []
    assert result.rejected_candidates == []
    assert result.selected_candidate is None
    assert "No matching products" in result.explanation
