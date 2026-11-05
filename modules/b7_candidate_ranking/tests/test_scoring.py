"""Tests for CandidateScorer normalization and scoring breakdown."""

from decimal import Decimal
import pytest
from modules.b7_candidate_ranking.models import (
    MandateSnapshot,
    ShoppingRequest,
)
from modules.b7_candidate_ranking.scoring import CandidateScorer
from modules.b7_candidate_ranking.tests.conftest import make_candidate_option


def test_scoring_bounded_and_granular(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test score is strictly within [0.0, 1.0] and contains complete breakdown."""
    candidate = make_candidate_option(price=Decimal("30.00"))
    scorer = CandidateScorer()
    score, breakdown, positive_factors, uncertain_info = scorer.score_candidate(
        candidate=candidate,
        request=default_request,
        mandate=default_mandate,
    )

    assert 0.0 <= score <= 1.0
    assert "price_factor" in breakdown
    assert "preferred_attributes_factor" in breakdown
    assert "brand_preference_factor" in breakdown
    assert "retailer_preference_factor" in breakdown
    assert "condition_factor" in breakdown
    assert "data_quality_factor" in breakdown
    assert len(positive_factors) > 0


def test_preferred_attributes_boost_score(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test candidate satisfying preferred attributes scores higher than candidate lacking them."""
    # default_request has preferred: {'color': 'black', 'usb_port': 'true'}
    cand_with_pref = make_candidate_option(
        product_id="cand_pref",
        attributes={"type": "desk", "dimmable": "true", "color": "black", "usb_port": "true"},
    )
    cand_without_pref = make_candidate_option(
        product_id="cand_nopref",
        attributes={"type": "desk", "dimmable": "true"},  # missing color and usb_port
    )

    scorer = CandidateScorer()
    score_with, breakdown_with, _, _ = scorer.score_candidate(cand_with_pref, default_request, default_mandate)
    score_without, breakdown_without, _, uncertain = scorer.score_candidate(cand_without_pref, default_request, default_mandate)

    assert score_with > score_without
    assert breakdown_with["preferred_attributes_factor"] > breakdown_without["preferred_attributes_factor"]
    assert any("usb_port" in u for u in uncertain)


def test_brand_preference_contribution(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test candidate matching preferred brand receives brand factor boost."""
    cand_pref_brand = make_candidate_option(brand="Lumina")
    cand_other_brand = make_candidate_option(brand="GenericLighting")

    scorer = CandidateScorer()
    score_pref, breakdown_pref, _, _ = scorer.score_candidate(cand_pref_brand, default_request, default_mandate)
    score_other, breakdown_other, _, _ = scorer.score_candidate(cand_other_brand, default_request, default_mandate)

    assert score_pref > score_other
    assert breakdown_pref["brand_preference_factor"] > breakdown_other["brand_preference_factor"]


def test_retailer_preference_contribution(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test offer from preferred merchant receives retailer factor boost."""
    # preferred_retailers: ['target.com', 'bestbuy.com']
    cand_pref_store = make_candidate_option(domain="target.com")
    cand_other_store = make_candidate_option(domain="walmart.com")

    scorer = CandidateScorer()
    score_pref, breakdown_pref, _, _ = scorer.score_candidate(cand_pref_store, default_request, default_mandate)
    score_other, breakdown_other, _, _ = scorer.score_candidate(cand_other_store, default_request, default_mandate)

    assert score_pref > score_other
    assert breakdown_pref["retailer_preference_factor"] > breakdown_other["retailer_preference_factor"]
