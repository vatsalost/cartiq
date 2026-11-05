"""Tests for deterministic candidate ranking and tie-breaking."""

from decimal import Decimal
import pytest
from modules.b7_candidate_ranking.models import (
    EligibilityStatus,
    MandateSnapshot,
    ShoppingRequest,
)
from modules.b7_candidate_ranking.ranking_service import RankingService
from modules.b7_candidate_ranking.tests.conftest import make_candidate_option


def test_candidates_ordered_by_score_descending(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test candidate with higher overall alignment ranks position 1."""
    # cand1 matches preferred brand and attributes at $30
    cand1 = make_candidate_option(
        product_id="prod_high",
        brand="Lumina",
        attributes={"type": "desk", "dimmable": "true", "color": "black", "usb_port": "true"},
        price=Decimal("30.00"),
    )
    # cand2 missing preferred attributes and brand at $38
    cand2 = make_candidate_option(
        product_id="prod_low",
        brand="Generic",
        attributes={"type": "desk", "dimmable": "true"},
        price=Decimal("38.00"),
    )

    ranking_svc = RankingService()
    ranked = ranking_svc.rank_candidates([cand2, cand1], default_request, default_mandate)

    assert len(ranked) == 2
    assert ranked[0].product_id == "prod_high"
    assert ranked[0].ranking_position == 1
    assert ranked[1].product_id == "prod_low"
    assert ranked[1].ranking_position == 2
    assert ranked[0].ranking_score > ranked[1].ranking_score


def test_tie_breaking_by_lower_price(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test identical scoring candidates are tie-broken by lower price."""
    cand_cheaper = make_candidate_option(
        product_id="prod_same_a",
        offer_key="off_cheap",
        price=Decimal("32.00"),
    )
    cand_expensive = make_candidate_option(
        product_id="prod_same_b",
        offer_key="off_exp",
        price=Decimal("36.00"),
    )

    # Force identical score by using empty request preferences
    neutral_request = ShoppingRequest(
        original_text="desk lamp",
        currency="USD",
        required_attributes={"type": "desk"},
        # No max_price, no preferred brands or attributes
    )

    ranking_svc = RankingService()
    ranked = ranking_svc.rank_candidates([cand_expensive, cand_cheaper], neutral_request, default_mandate)

    assert ranked[0].price_amount == Decimal("32.00")
    assert ranked[1].price_amount == Decimal("36.00")
    assert ranked[0].ranking_position == 1


def test_multiple_offers_for_same_canonical_product(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Test same canonical product listed by two different retailers."""
    offer_target = make_candidate_option(
        product_id="prod_shared_101",
        offer_key="off_tgt",
        domain="target.com",
        price=Decimal("29.99"),
    )
    offer_bestbuy = make_candidate_option(
        product_id="prod_shared_101",
        offer_key="off_bb",
        domain="bestbuy.com",
        price=Decimal("34.99"),
    )

    ranking_svc = RankingService()
    ranked = ranking_svc.rank_candidates([offer_bestbuy, offer_target], default_request, default_mandate)

    assert len(ranked) == 2
    assert ranked[0].offer_key == "off_tgt"
    assert ranked[0].domain == "target.com"
    assert ranked[1].offer_key == "off_bb"


def test_tie_breaking_alphabetical_fallback(default_request: ShoppingRequest):
    """Test that truly identical candidates tie-break alphabetically on candidate_id."""
    cand_z = make_candidate_option(product_id="prod_z", offer_key="off_1", price=Decimal("30.00"))
    cand_a = make_candidate_option(product_id="prod_a", offer_key="off_1", price=Decimal("30.00"))

    ranking_svc = RankingService()
    ranked = ranking_svc.rank_candidates([cand_z, cand_a], default_request)

    assert ranked[0].candidate_id == "prod_a:off_1"
    assert ranked[1].candidate_id == "prod_z:off_1"
