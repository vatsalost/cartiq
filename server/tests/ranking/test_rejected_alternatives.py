"""Tests for rejected alternatives and concrete rejection code preservation."""

from decimal import Decimal
import pytest
from server.app.services.ranking.comparison_service import ComparisonService
from server.app.services.ranking.models import (
    EligibilityStatus,
    MandateSnapshot,
    RejectionCode,
    ShoppingRequest,
)
from server.tests.ranking.conftest import make_candidate_option


def test_rejected_alternatives_retain_codes_and_reasons(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Verify that excluded candidates contain all specific rejection codes."""
    # Option 1: Eligible
    cand_valid = make_candidate_option(product_id="valid_1", price=Decimal("35.00"))
    # Option 2: Out of stock
    cand_oos = make_candidate_option(product_id="oos_2", availability="OutOfStock")
    # Option 3: Over price cap
    cand_expensive = make_candidate_option(product_id="exp_3", price=Decimal("75.00"))

    svc = ComparisonService()
    result = svc.compare_and_rank(
        request=default_request,
        candidates=[cand_valid, cand_oos, cand_expensive],
        mandate=default_mandate,
    )

    assert len(result.ranked_candidates) == 1
    assert result.selected_candidate.product_id == "valid_1"

    rejected = svc.get_rejected_alternatives(result)
    assert len(rejected) == 2

    rejected_map = {r.product_id: [reason.code for reason in r.rejection_reasons] for r in rejected}
    assert RejectionCode.OUT_OF_STOCK in rejected_map["oos_2"]
    assert RejectionCode.ABOVE_REQUEST_PRICE_LIMIT in rejected_map["exp_3"]
    assert RejectionCode.ABOVE_PER_ITEM_CAP in rejected_map["exp_3"]


def test_ineligible_candidates_never_rank_above_eligible(default_request: ShoppingRequest, default_mandate: MandateSnapshot):
    """Ensure that ineligible candidates have score 0.0 and are completely excluded from ranked list."""
    # Even if an ineligible offer has a lower price, it must never appear in ranked_candidates
    cand_cheap_but_oos = make_candidate_option(
        product_id="cheap_oos",
        price=Decimal("15.00"),
        availability="OutOfStock",
    )
    cand_normal_eligible = make_candidate_option(
        product_id="normal_instock",
        price=Decimal("39.99"),
        availability="InStock",
    )

    svc = ComparisonService()
    result = svc.compare_and_rank(
        request=default_request,
        candidates=[cand_cheap_but_oos, cand_normal_eligible],
        mandate=default_mandate,
    )

    # Only the eligible candidate is in ranked_candidates
    assert len(result.ranked_candidates) == 1
    assert result.ranked_candidates[0].product_id == "normal_instock"
    assert result.ranked_candidates[0].eligibility_status == EligibilityStatus.ELIGIBLE

    # The ineligible candidate is in rejected_candidates
    assert len(result.rejected_candidates) == 1
    assert result.rejected_candidates[0].product_id == "cheap_oos"
    assert result.rejected_candidates[0].eligibility_status == EligibilityStatus.INELIGIBLE
    assert result.rejected_candidates[0].ranking_score == 0.0
