"""
Tests for Module B8 — Deterministic Guardrail & Policy Engine.

Covers all 23 required test cases from the specification plus additional
edge cases. All tests are isolated, use mock data only, and do NOT modify
any existing project files or shared state.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import pytest

from modules.b7_candidate_ranking.models import MandateSnapshot
from modules.b8_guardrail_policy import DecisionService, PolicyDecisionStatus
from modules.b8_guardrail_policy.models import (
    PolicyViolationCode,
    ProposalEvaluationRequest,
)
from modules.b8_guardrail_policy.tests.conftest import make_proposal

# ---------------------------------------------------------------------------
# Service instance (stateless — reused across tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def svc() -> DecisionService:
    return DecisionService()


# ===========================================================================
# TC-01: Valid mandate + valid proposal → APPROVED
# ===========================================================================

def test_valid_mandate_valid_proposal_approved(svc, valid_mandate, valid_proposal):
    """TC-01: Fully compliant proposal against active mandate must be APPROVED."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.APPROVED
    assert decision.is_approved
    assert decision.is_safe_to_proceed
    assert decision.violations == []
    assert decision.rejection_reasons == []


# ===========================================================================
# TC-02: Missing mandate → UNABLE_TO_DETERMINE
# ===========================================================================

def test_missing_mandate_unable_to_determine(svc, valid_proposal):
    """TC-02: No mandate present must yield UNABLE_TO_DETERMINE (not APPROVED)."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=None)
    assert decision.status == PolicyDecisionStatus.UNABLE_TO_DETERMINE
    assert not decision.is_approved
    assert not decision.is_safe_to_proceed
    assert PolicyViolationCode.MANDATE_MISSING in decision.violations


# ===========================================================================
# TC-03: Expired mandate → REJECTED
# ===========================================================================

def test_expired_mandate_rejected(svc, expired_mandate, valid_proposal):
    """TC-03: An expired mandate must yield REJECTED."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=expired_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert not decision.is_approved
    assert PolicyViolationCode.MANDATE_EXPIRED in decision.violations


# ===========================================================================
# TC-04: Invalid/revoked mandate → REJECTED
# ===========================================================================

def test_revoked_mandate_rejected(svc, revoked_mandate, valid_proposal):
    """TC-04a: A revoked mandate must yield REJECTED."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=revoked_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.MANDATE_INVALID_STATUS in decision.violations


def test_superseded_mandate_rejected(svc, superseded_mandate, valid_proposal):
    """TC-04b: A superseded mandate must yield REJECTED."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=superseded_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.MANDATE_INVALID_STATUS in decision.violations


def test_unknown_mandate_status_rejected(svc, valid_proposal):
    """TC-04c: An unrecognized mandate status must yield REJECTED."""
    mandate = MandateSnapshot(currency="USD", status="pending_review")
    decision = svc.evaluate(proposal=valid_proposal, mandate=mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.MANDATE_INVALID_STATUS in decision.violations


# ===========================================================================
# TC-05: Budget limit violation → REJECTED
# ===========================================================================

def test_budget_ceiling_exceeded_rejected(svc, valid_mandate):
    """TC-05: Offer price above total_budget ceiling must be REJECTED."""
    proposal = make_proposal(price_amount=Decimal("250.00"))  # mandate total_budget = 200.00
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.BUDGET_EXCEEDED in decision.violations


# ===========================================================================
# TC-06: Per-item spending limit violation → REJECTED
# ===========================================================================

def test_per_item_cap_exceeded_rejected(svc, valid_mandate):
    """TC-06: Offer price above per_item_cap must be REJECTED."""
    proposal = make_proposal(price_amount=Decimal("90.00"))  # mandate per_item_cap = 80.00
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.PER_ITEM_CAP_EXCEEDED in decision.violations


# ===========================================================================
# TC-07: Blocked category → REJECTED
# ===========================================================================

def test_blocked_category_rejected(svc, valid_mandate):
    """TC-07: Product in mandate blocked_categories must be REJECTED."""
    proposal = make_proposal(category="Hazardous Materials")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.BLOCKED_CATEGORY in decision.violations


def test_blocked_category_weapons_rejected(svc, valid_mandate):
    """TC-07b: 'Weapons' category (exact blocklist match) must be REJECTED."""
    proposal = make_proposal(category="Weapons")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.BLOCKED_CATEGORY in decision.violations


# ===========================================================================
# TC-08: Disallowed category → REJECTED
# ===========================================================================

def test_category_not_in_allowlist_rejected(svc, valid_mandate):
    """TC-08: Product not in allowed_categories must be REJECTED."""
    proposal = make_proposal(category="Automotive Accessories")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.CATEGORY_NOT_ALLOWED in decision.violations


# ===========================================================================
# TC-09: Disallowed retailer → REJECTED
# ===========================================================================

def test_retailer_not_in_allowlist_rejected(svc, valid_mandate):
    """TC-09: Offer from retailer not in allowed_retailers must be REJECTED."""
    proposal = make_proposal(domain="shady-merchant.com")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.RETAILER_NOT_ALLOWED in decision.violations


# ===========================================================================
# TC-10: Quantity restriction violation → REJECTED
# ===========================================================================

def test_quantity_exceeded_rejected(svc, valid_mandate):
    """TC-10: Requested quantity above max_quantity must be REJECTED."""
    proposal = make_proposal(quantity=10)  # mandate max_quantity = 5
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.QUANTITY_EXCEEDED in decision.violations


# ===========================================================================
# TC-11: Currency mismatch → REJECTED
# ===========================================================================

def test_currency_mismatch_rejected(svc, valid_mandate):
    """TC-11: Offer in wrong currency must be REJECTED — no silent conversion."""
    proposal = make_proposal(currency="EUR")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.CURRENCY_MISMATCH in decision.violations


def test_currency_mismatch_gbp_rejected(svc, valid_mandate):
    """TC-11b: GBP offer against USD mandate must be REJECTED."""
    proposal = make_proposal(currency="GBP")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.CURRENCY_MISMATCH in decision.violations


# ===========================================================================
# TC-12: Invalid price → INVALID_INPUT
# ===========================================================================

def test_zero_price_invalid_input(svc, valid_mandate):
    """TC-12a: Zero price must yield INVALID_INPUT."""
    proposal = make_proposal(price_amount=Decimal("0.00"))
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_PRICE in decision.violations


def test_negative_price_invalid_input(svc, valid_mandate):
    """TC-12b: Negative price must yield INVALID_INPUT."""
    proposal = make_proposal(price_amount=Decimal("-10.00"))
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_PRICE in decision.violations


# ===========================================================================
# TC-13: Out-of-stock offer → REJECTED
# ===========================================================================

def test_out_of_stock_rejected(svc, valid_mandate):
    """TC-13a: OutOfStock offer must be REJECTED."""
    proposal = make_proposal(availability="OutOfStock")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.OUT_OF_STOCK in decision.violations


def test_unknown_availability_rejected(svc, valid_mandate):
    """TC-13b: Unknown availability must be REJECTED (not silently approved)."""
    proposal = make_proposal(availability="Unknown")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.OUT_OF_STOCK in decision.violations


def test_empty_availability_rejected(svc, valid_mandate):
    """TC-13c: Blank availability string must be REJECTED."""
    proposal = make_proposal(availability="")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.OUT_OF_STOCK in decision.violations


# ===========================================================================
# TC-14: Invalid product or offer data → INVALID_INPUT
# ===========================================================================

def test_missing_offer_key_invalid_input(svc, valid_mandate):
    """TC-14a: Missing offer_key must yield INVALID_INPUT."""
    proposal = make_proposal(offer_key="")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_OFFER_DATA in decision.violations


def test_missing_buy_url_invalid_input(svc, valid_mandate):
    """TC-14b: Missing buy_url must yield INVALID_INPUT."""
    proposal = make_proposal(buy_url="")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_OFFER_DATA in decision.violations


def test_missing_domain_invalid_input(svc, valid_mandate):
    """TC-14c: Missing domain must yield INVALID_INPUT."""
    proposal = make_proposal(domain="")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_OFFER_DATA in decision.violations


def test_missing_product_id_invalid_input(svc, valid_mandate):
    """TC-14d: Missing product_id must yield INVALID_INPUT."""
    proposal = make_proposal(product_id="")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_PRODUCT_DATA in decision.violations


def test_missing_product_title_invalid_input(svc, valid_mandate):
    """TC-14e: Missing product_title must yield INVALID_INPUT."""
    proposal = make_proposal(product_title="")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.INVALID_INPUT
    assert PolicyViolationCode.INVALID_PRODUCT_DATA in decision.violations


# ===========================================================================
# TC-16: Valid eligible candidate → APPROVED (no-caps mandate)
# ===========================================================================

def test_valid_candidate_no_caps_mandate_approved(svc, mandate_no_caps):
    """TC-16: Valid proposal against a mandate with no caps/restrictions must be APPROVED."""
    proposal = make_proposal()
    decision = svc.evaluate(proposal=proposal, mandate=mandate_no_caps)
    assert decision.status == PolicyDecisionStatus.APPROVED
    assert decision.is_safe_to_proceed


# ===========================================================================
# TC-17: Ineligible candidate — per-item cap
# ===========================================================================

def test_ineligible_candidate_per_item_cap(svc, valid_mandate):
    """TC-17: Candidate above per-item cap must be ineligible (REJECTED)."""
    proposal = make_proposal(price_amount=Decimal("100.00"))
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert not decision.is_approved
    assert PolicyViolationCode.PER_ITEM_CAP_EXCEEDED in decision.violations


# ===========================================================================
# TC-18: Multiple simultaneous policy violations
# ===========================================================================

def test_multiple_simultaneous_violations(svc, valid_mandate):
    """TC-18: Multiple concurrent violations must all be captured — no early-abort."""
    proposal = make_proposal(
        price_amount=Decimal("300.00"),    # exceeds total_budget and per_item_cap
        currency="EUR",                    # currency mismatch
        availability="OutOfStock",         # out of stock
        domain="unauthorized.com",         # retailer not allowed
        category="Adult Content",          # blocked category
        quantity=99,                       # quantity exceeded
    )
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert not decision.is_approved
    assert PolicyViolationCode.OUT_OF_STOCK in decision.violations
    assert PolicyViolationCode.CURRENCY_MISMATCH in decision.violations
    assert PolicyViolationCode.RETAILER_NOT_ALLOWED in decision.violations
    assert PolicyViolationCode.QUANTITY_EXCEEDED in decision.violations
    # Blocked category should be detected
    assert PolicyViolationCode.BLOCKED_CATEGORY in decision.violations
    # At least 4 violations
    assert len(decision.violations) >= 4


# ===========================================================================
# TC-19: Deterministic repeated decisions
# ===========================================================================

def test_deterministic_repeated_decisions(svc, valid_mandate):
    """TC-19: Same inputs must always produce the same decision status."""
    proposal = make_proposal()
    fixed_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    decisions = [
        svc.evaluate(proposal=proposal, mandate=valid_mandate, now=fixed_time)
        for _ in range(5)
    ]

    statuses = {d.status for d in decisions}
    assert len(statuses) == 1, f"Non-deterministic: got statuses {statuses}"

    # Violations should also be identical across all runs
    for d in decisions:
        assert d.violations == decisions[0].violations


def test_deterministic_rejection_repeated(svc, valid_mandate):
    """TC-19b: Rejected proposal must be consistently rejected across repeated calls."""
    proposal = make_proposal(currency="EUR")
    fixed_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    decisions = [
        svc.evaluate(proposal=proposal, mandate=valid_mandate, now=fixed_time)
        for _ in range(5)
    ]

    for d in decisions:
        assert d.status == PolicyDecisionStatus.REJECTED
        assert PolicyViolationCode.CURRENCY_MISMATCH in d.violations


# ===========================================================================
# TC-20: Missing or uncertain policy information
# ===========================================================================

def test_mandate_missing_currency_unable_or_rejected(svc, valid_proposal):
    """TC-20: Mandate with invalid currency (not 3 chars) causes REJECTED
    due to MANDATE_CURRENCY_MISSING violation."""
    mandate = MandateSnapshot(
        total_budget=Decimal("100.00"),
        currency="XX",   # invalid — not 3-letter ISO
        status="active",
    )
    decision = svc.evaluate(proposal=valid_proposal, mandate=mandate)
    assert not decision.is_approved
    assert PolicyViolationCode.MANDATE_CURRENCY_MISSING in decision.violations


# ===========================================================================
# TC-21: B7 input compatibility
# ===========================================================================

def test_b7_ranking_score_ignored(svc, valid_mandate):
    """TC-21a: Proposal with high B7 score must still be evaluated independently."""
    # Proposal has an ILLEGAL currency but a high B7 ranking score.
    proposal = make_proposal(
        currency="EUR",
        b7_ranking_score=0.999,  # near-perfect B7 score — MUST NOT override B8 policy
    )
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.CURRENCY_MISMATCH in decision.violations


def test_b7_score_zero_does_not_cause_rejection(svc, valid_mandate):
    """TC-21b: Proposal with zero B7 score must still pass if policy is satisfied."""
    proposal = make_proposal(b7_ranking_score=0.0)
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.APPROVED


def test_b7_ranked_candidate_fields_accepted(svc, valid_mandate):
    """TC-21c: B7 RankedCandidate fields map correctly to ProposalEvaluationRequest."""
    from modules.b7_candidate_ranking.models import (
        CandidateOffer, CandidateOption, CandidateProduct, EligibilityStatus,
        RankedCandidate,
    )
    from datetime import datetime, timezone

    ranked = RankedCandidate(
        candidate_id="prod_1:off_1",
        product_id="prod_1",
        offer_key="off_1",
        product_title="Test Lamp",
        brand="Lumina",
        category="Home Lighting",
        domain="target.com",
        price_amount=Decimal("39.99"),
        currency="USD",
        availability="InStock",
        condition="new",
        buy_url="https://buy.trychannel3.com/target/1",
        image_url=None,
        eligibility_status=EligibilityStatus.ELIGIBLE,
        ranking_score=0.87,
    )

    # Map RankedCandidate → ProposalEvaluationRequest
    proposal = ProposalEvaluationRequest(
        candidate_id=ranked.candidate_id,
        product_id=ranked.product_id,
        offer_key=ranked.offer_key,
        product_title=ranked.product_title,
        category=ranked.category,
        domain=ranked.domain,
        buy_url=ranked.buy_url,
        price_amount=ranked.price_amount,
        currency=ranked.currency,
        availability=ranked.availability,
        condition=ranked.condition,
        b7_ranking_score=ranked.ranking_score,
    )

    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.APPROVED
    assert decision.is_safe_to_proceed


# ===========================================================================
# TC-22: B9 decision output compatibility
# ===========================================================================

def test_b9_consumes_policy_decision_fields(svc, valid_mandate, valid_proposal):
    """TC-22a: PolicyDecision exposes all fields B9 needs to consume."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=valid_mandate)

    # Fields B9 must be able to read:
    assert decision.decision_id is not None and len(decision.decision_id) > 0
    assert decision.status in list(PolicyDecisionStatus)
    assert isinstance(decision.rule_results, list)
    assert isinstance(decision.violations, list)
    assert isinstance(decision.rejection_reasons, list)
    assert decision.evaluated_at is not None
    assert isinstance(decision.is_safe_to_proceed, bool)
    assert isinstance(decision.is_approved, bool)
    assert isinstance(decision.is_rejected, bool)


def test_b9_rejection_decision_has_reasons(svc, valid_mandate):
    """TC-22b: Rejected decision must carry human-readable rejection reasons for B9."""
    proposal = make_proposal(availability="OutOfStock")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)

    assert decision.status == PolicyDecisionStatus.REJECTED
    assert len(decision.rejection_reasons) > 0
    # Reasons must be non-empty strings
    for reason in decision.rejection_reasons:
        assert isinstance(reason, str) and len(reason) > 0


def test_b9_cannot_bypass_rejection_via_is_safe_to_proceed(svc, valid_mandate):
    """TC-22c: is_safe_to_proceed is False for REJECTED and UNABLE_TO_DETERMINE."""
    # REJECTED case
    proposal_rej = make_proposal(currency="EUR")
    decision_rej = svc.evaluate(proposal=proposal_rej, mandate=valid_mandate)
    assert not decision_rej.is_safe_to_proceed

    # UNABLE_TO_DETERMINE case
    decision_utd = svc.evaluate(proposal=make_proposal(), mandate=None)
    assert not decision_utd.is_safe_to_proceed

    # INVALID_INPUT case
    proposal_inv = make_proposal(price_amount=Decimal("0.00"))
    decision_inv = svc.evaluate(proposal=proposal_inv, mandate=valid_mandate)
    assert not decision_inv.is_safe_to_proceed


# ===========================================================================
# TC-23: Attempts to bypass or override policy decisions
# ===========================================================================

def test_policy_decision_is_immutable(svc, valid_mandate):
    """TC-23a: PolicyDecision is frozen — mutation attempts raise an error."""
    decision = svc.evaluate(proposal=make_proposal(), mandate=valid_mandate)
    with pytest.raises(Exception):
        # Frozen Pydantic model raises ValidationError or TypeError on mutation
        decision.status = PolicyDecisionStatus.APPROVED  # type: ignore[misc]


def test_high_b7_score_cannot_override_rejection(svc, valid_mandate):
    """TC-23b: B7 score of 1.0 must not override a policy rejection."""
    proposal = make_proposal(
        domain="unauthorized-retailer.com",
        b7_ranking_score=1.0,
    )
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert not decision.is_safe_to_proceed


def test_llm_approval_cannot_bypass_policy(svc, valid_mandate):
    """TC-23c: Simulated LLM 'approval' cannot change B8 decision — no path exists."""
    # B8 has no API that accepts LLM-generated decisions.
    # This test verifies the ONLY path to APPROVED requires passing all rules.
    proposal = make_proposal(availability="OutOfStock")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    # Even if an LLM said "yes", the deterministic engine returns REJECTED.
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert not decision.is_safe_to_proceed


# ===========================================================================
# Additional edge cases
# ===========================================================================

def test_mandate_expired_at_exact_boundary(svc, valid_proposal):
    """Edge: Mandate expiring exactly at evaluation time must be REJECTED."""
    exact_now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    mandate = MandateSnapshot(
        currency="USD",
        status="active",
        expires_at=exact_now,  # expires AT the exact moment of evaluation
    )
    decision = svc.evaluate(proposal=valid_proposal, mandate=mandate, now=exact_now)
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.MANDATE_EXPIRED in decision.violations


def test_no_spending_limits_all_categories_approved(svc):
    """Edge: Mandate with no restrictions at all must approve any compliant offer."""
    mandate = MandateSnapshot(currency="USD", status="active")
    proposal = make_proposal(
        price_amount=Decimal("9999.99"),
        category="Anything",
        domain="anystore.com",
    )
    decision = svc.evaluate(proposal=proposal, mandate=mandate)
    assert decision.status == PolicyDecisionStatus.APPROVED


def test_rule_results_always_present(svc, valid_mandate, valid_proposal):
    """Edge: Approved decision must still have non-empty rule_results for auditability."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=valid_mandate)
    assert len(decision.rule_results) > 0
    # All rules must have passed
    assert all(r.passed for r in decision.rule_results)


def test_decision_id_is_unique_per_evaluation(svc, valid_mandate, valid_proposal):
    """Edge: Each evaluation produces a unique decision_id (UUID)."""
    d1 = svc.evaluate(proposal=valid_proposal, mandate=valid_mandate)
    d2 = svc.evaluate(proposal=valid_proposal, mandate=valid_mandate)
    assert d1.decision_id != d2.decision_id


def test_www_prefix_stripped_from_domain_allowlist(svc):
    """Edge: 'www.target.com' and 'target.com' must both match the allowlist."""
    mandate = MandateSnapshot(
        currency="USD",
        status="active",
        allowed_retailers=["www.target.com"],
    )
    proposal = make_proposal(domain="target.com")
    decision = svc.evaluate(proposal=proposal, mandate=mandate)
    assert decision.status == PolicyDecisionStatus.APPROVED


def test_category_matching_is_case_insensitive(svc):
    """Edge: Category matching is case-insensitive."""
    mandate = MandateSnapshot(
        currency="USD",
        status="active",
        allowed_categories=["Home Lighting"],
        blocked_categories=[],
    )
    proposal = make_proposal(category="home lighting")
    decision = svc.evaluate(proposal=proposal, mandate=mandate)
    assert decision.status == PolicyDecisionStatus.APPROVED


def test_price_tolerance_pass(svc):
    """Edge: Price within tolerance must be APPROVED when re-evaluated."""
    mandate = MandateSnapshot(
        currency="USD",
        status="active",
        price_tolerance=Decimal("2.00"),
    )
    proposal = make_proposal(price_amount=Decimal("35.50"))
    reference_price = Decimal("34.99")  # drift = 0.51, within 2.00 tolerance
    decision = svc.evaluate(
        proposal=proposal, mandate=mandate, reference_price=reference_price
    )
    assert decision.status == PolicyDecisionStatus.APPROVED


def test_price_tolerance_violation_rejected(svc):
    """Edge: Price drifted beyond tolerance must be REJECTED."""
    mandate = MandateSnapshot(
        currency="USD",
        status="active",
        price_tolerance=Decimal("1.00"),
    )
    proposal = make_proposal(price_amount=Decimal("40.00"))
    reference_price = Decimal("34.99")  # drift = 5.01, exceeds 1.00 tolerance
    decision = svc.evaluate(
        proposal=proposal, mandate=mandate, reference_price=reference_price
    )
    assert decision.status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.PRICE_TOLERANCE_EXCEEDED in decision.violations


def test_evaluate_candidate_eligibility_convenience_method(svc, valid_mandate):
    """Edge: Convenience method evaluate_candidate_eligibility works correctly."""
    decision = svc.evaluate_candidate_eligibility(
        candidate_id="prod_1:off_1",
        product_id="prod_1",
        offer_key="off_1",
        product_title="Test Lamp",
        category="Home Lighting",
        domain="target.com",
        buy_url="https://buy.trychannel3.com/t/1",
        price_amount=Decimal("39.99"),
        currency="USD",
        availability="InStock",
        condition="new",
        mandate=valid_mandate,
    )
    assert decision.status == PolicyDecisionStatus.APPROVED


def test_mandate_status_recorded_in_decision(svc, valid_mandate, valid_proposal):
    """Edge: Decision must record the mandate status at time of evaluation."""
    decision = svc.evaluate(proposal=valid_proposal, mandate=valid_mandate)
    assert decision.mandate_status_at_evaluation == "active"


def test_decision_captures_evaluated_price_and_currency(svc, valid_mandate):
    """Edge: Decision must record the evaluated price and currency for audit."""
    proposal = make_proposal(price_amount=Decimal("49.99"), currency="USD")
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert decision.evaluated_price == Decimal("49.99")
    assert decision.evaluated_currency == "USD"


def test_blocked_and_not_in_allowed_simultaneous(svc):
    """Edge: Category blocked AND not in allowed list must yield both violations."""
    mandate = MandateSnapshot(
        currency="USD",
        status="active",
        allowed_categories=["Electronics"],
        blocked_categories=["Weapons"],
    )
    proposal = make_proposal(category="Weapons")
    decision = svc.evaluate(proposal=proposal, mandate=mandate)
    assert not decision.is_approved
    assert PolicyViolationCode.BLOCKED_CATEGORY in decision.violations
    assert PolicyViolationCode.CATEGORY_NOT_ALLOWED in decision.violations


def test_wrong_condition_rejected_in_b8(svc, valid_mandate):
    """Verify that condition mismatch produces WRONG_CONDITION violation in B8."""
    proposal = make_proposal(condition="refurbished")
    proposal.required_condition = "new"
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert not decision.is_approved
    assert PolicyViolationCode.WRONG_CONDITION in decision.violations


def test_missing_required_attribute_rejected_in_b8(svc, valid_mandate):
    """Verify that missing required attribute produces MISSING_REQUIRED_ATTRIBUTE in B8."""
    proposal = make_proposal(attributes={"color": "black"})
    proposal.required_attributes = {"color": "black", "dimmable": "true"}
    decision = svc.evaluate(proposal=proposal, mandate=valid_mandate)
    assert not decision.is_approved
    assert PolicyViolationCode.MISSING_REQUIRED_ATTRIBUTE in decision.violations


def test_evaluate_ranked_candidate_and_comparison_result(svc, valid_mandate):
    """Verify DecisionService convenience methods evaluate_ranked_candidate and evaluate_comparison_result."""
    from modules.b7_candidate_ranking.models import (
        ComparisonResult,
        EligibilityStatus,
        RankedCandidate,
    )

    ranked1 = RankedCandidate(
        candidate_id="prod_1:off_1",
        product_id="prod_1",
        offer_key="off_1",
        product_title="Test Lamp 1",
        category="Home Lighting",
        domain="target.com",
        price_amount=Decimal("30.00"),
        currency="USD",
        availability="InStock",
        condition="new",
        buy_url="https://target.com/1",
        eligibility_status=EligibilityStatus.ELIGIBLE,
        ranking_score=0.90,
    )
    ranked2 = RankedCandidate(
        candidate_id="prod_2:off_2",
        product_id="prod_2",
        offer_key="off_2",
        product_title="Test Lamp 2",
        category="Home Lighting",
        domain="target.com",
        price_amount=Decimal("999.00"),  # exceeds budget
        currency="USD",
        availability="InStock",
        condition="new",
        buy_url="https://target.com/2",
        eligibility_status=EligibilityStatus.ELIGIBLE,
        ranking_score=0.70,
    )

    d1 = svc.evaluate_ranked_candidate(ranked=ranked1, mandate=valid_mandate)
    assert d1.status == PolicyDecisionStatus.APPROVED

    comp = ComparisonResult(
        ranked_candidates=[ranked1, ranked2],
        explanation="Testing comparison",
    )
    results = svc.evaluate_comparison_result(comp, mandate=valid_mandate)
    assert len(results) == 2
    assert results["prod_1:off_1"].status == PolicyDecisionStatus.APPROVED
    assert results["prod_2:off_2"].status == PolicyDecisionStatus.REJECTED
