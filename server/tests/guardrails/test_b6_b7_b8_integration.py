"""End-to-end integration tests between B6 (Channel3), B7 (Ranking), and B8 (Policy Guardrail).

Tests verify that:
1. B6 NormalizedProduct instances adapt cleanly into B7 CandidateOptions.
2. B7 ranks and compares candidates with explanations.
3. B8 acts as the authoritative final policy gate on B7 ranking output.
4. B7 scores cannot override B8 policy rejections.
5. All three modules operate seamlessly without external/separate integration packages.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import pytest

from server.app.services.discovery.models.offer import NormalizedOffer
from server.app.services.discovery.models.product import NormalizedProduct
from server.app.services.ranking.comparison_service import ComparisonService
from server.app.services.ranking.models import (
    MandateSnapshot,
    ShoppingRequest,
)
from server.app.services.guardrails.decision_service import DecisionService
from server.app.services.guardrails.models import (
    PolicyDecisionStatus,
    PolicyViolationCode,
)


def _make_b6_product(
    product_id: str,
    title: str,
    brand: str = "Lumina",
    category: str = "Home Lighting",
    attributes: Optional[dict] = None,
    offers: Optional[list[NormalizedOffer]] = None,
) -> NormalizedProduct:
    """Helper creating a B6 NormalizedProduct."""
    attrs = attributes or {"type": "desk", "dimmable": "true", "color": "black"}
    return NormalizedProduct(
        product_id=product_id,
        title=title,
        brand=brand,
        category=category,
        description=f"Description for {title}",
        attributes=attrs,
        offers=offers or [],
        image_url=f"https://img.carti.ai/{product_id}.jpg",
        observed_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def b7_comparison_service() -> ComparisonService:
    return ComparisonService()


@pytest.fixture
def b8_decision_service() -> DecisionService:
    return DecisionService()


@pytest.fixture
def shopping_request() -> ShoppingRequest:
    return ShoppingRequest(
        original_text="Need a dimmable LED desk lamp under $50",
        category="Home Lighting",
        required_attributes={"type": "desk", "dimmable": "true"},
        preferred_attributes={"color": "black"},
        max_price=Decimal("50.00"),
        currency="USD",
        preferred_brands=["Lumina"],
        preferred_retailers=["target.com", "bestbuy.com"],
        required_condition="new",
    )


@pytest.fixture
def valid_mandate() -> MandateSnapshot:
    return MandateSnapshot(
        total_budget=Decimal("150.00"),
        currency="USD",
        per_item_cap=Decimal("60.00"),
        allowed_retailers=["target.com", "bestbuy.com", "amazon.com", "walmart.com"],
        blocked_categories=["Weapons", "Hazardous"],
        allowed_categories=["Home Lighting", "Office Supplies"],
        max_quantity=4,
        price_tolerance=Decimal("2.00"),
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )


def test_b6_to_b7_to_b8_end_to_end_flow(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """Verify B6 NormalizedProduct -> B7 Ranking -> B8 Policy Approval flow."""
    # 1. B6 Product & Offer
    b6_prod = _make_b6_product(
        product_id="prod_lamp_01",
        title="Lumina Touch Desk Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_target_01",
                domain="target.com",
                price_amount=Decimal("34.99"),
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            )
        ],
    )

    # 2. B7 Adapt & Compare
    candidates = b7_comparison_service.adapt_b6_products([b6_prod])
    assert len(candidates) == 1
    assert candidates[0].product.product_id == "prod_lamp_01"

    comparison = b7_comparison_service.compare_and_rank(
        request=shopping_request,
        candidates=candidates,
    )
    assert len(comparison.ranked_candidates) == 1
    top_candidate = comparison.selected_candidate
    assert top_candidate is not None
    assert top_candidate.product_title == "Lumina Touch Desk Lamp"

    # 3. B8 Authoritative Policy Evaluation
    decisions = b8_decision_service.evaluate_comparison_result(
        comparison_result=comparison,
        mandate=valid_mandate,
        quantity=2,
    )

    assert top_candidate.candidate_id in decisions
    decision = decisions[top_candidate.candidate_id]
    assert decision.status == PolicyDecisionStatus.APPROVED
    assert decision.is_safe_to_proceed is True
    assert decision.evaluated_price == Decimal("34.99")
    assert decision.evaluated_currency == "USD"


def test_b6_multiple_offers_ranked_in_b7_and_authorized_in_b8(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """Verify multiple offers for one product are preserved as candidates and ranked correctly."""
    b6_prod = _make_b6_product(
        product_id="prod_multi_offer",
        title="Multi-Retailer Desk Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_target_more_exp",
                domain="target.com",
                price_amount=Decimal("39.99"),
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            ),
            NormalizedOffer(
                offer_key="off_bestbuy_cheaper",
                domain="bestbuy.com",
                price_amount=Decimal("29.99"),  # Lower price
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://bestbuy.com/lamp",
            ),
        ],
    )

    candidates = b7_comparison_service.adapt_b6_products([b6_prod])
    assert len(candidates) == 2

    comparison = b7_comparison_service.compare_and_rank(
        request=shopping_request,
        candidates=candidates,
    )
    assert len(comparison.ranked_candidates) == 2
    # The cheaper BestBuy offer should rank higher
    assert comparison.ranked_candidates[0].domain == "bestbuy.com"

    decisions = b8_decision_service.evaluate_comparison_result(
        comparison_result=comparison,
        mandate=valid_mandate,
    )

    bestbuy_cand = comparison.ranked_candidates[0]
    target_cand = comparison.ranked_candidates[1]

    assert decisions[bestbuy_cand.candidate_id].status == PolicyDecisionStatus.APPROVED
    assert decisions[target_cand.candidate_id].status == PolicyDecisionStatus.APPROVED


def test_b8_authoritative_rejection_overrides_high_b7_score(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """CRITICAL: B7 ranking score CANNOT override B8 policy rejections.

    A cheaper candidate on an unapproved domain ranks #1 in B7, but B8 rejects it
    while approving the compliant #2 candidate.
    """
    prod_unapproved = _make_b6_product(
        product_id="prod_cheap_unapproved",
        title="Ultra Cheap Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_unapproved",
                domain="unapproved-shop.com",  # Not in allowed_retailers
                price_amount=Decimal("19.99"),  # Cheaper -> high B7 score
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://unapproved-shop.com/lamp",
            )
        ],
    )
    prod_approved = _make_b6_product(
        product_id="prod_target_approved",
        title="Standard Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_target",
                domain="target.com",  # In allowed_retailers
                price_amount=Decimal("35.00"),
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            )
        ],
    )

    # Remove preferred retailers in request so unapproved shop ranks #1 purely on price in B7
    req = shopping_request.model_copy(update={"preferred_retailers": []})
    candidates = b7_comparison_service.adapt_b6_products([prod_unapproved, prod_approved])

    comparison = b7_comparison_service.compare_and_rank(request=req, candidates=candidates)

    # In B7, the unapproved shop ranks #1 due to lower price
    assert comparison.ranked_candidates[0].domain == "unapproved-shop.com"
    assert comparison.ranked_candidates[1].domain == "target.com"

    decisions = b8_decision_service.evaluate_comparison_result(
        comparison_result=comparison,
        mandate=valid_mandate,
    )

    unapproved_id = comparison.ranked_candidates[0].candidate_id
    target_id = comparison.ranked_candidates[1].candidate_id

    # Decision 1 (unapproved shop) was REJECTED by B8 despite #1 ranking
    assert decisions[unapproved_id].status == PolicyDecisionStatus.REJECTED
    assert decisions[unapproved_id].is_safe_to_proceed is False
    assert PolicyViolationCode.RETAILER_NOT_ALLOWED in decisions[unapproved_id].violations

    # Decision 2 (Target) was APPROVED by B8
    assert decisions[target_id].status == PolicyDecisionStatus.APPROVED
    assert decisions[target_id].is_safe_to_proceed is True


def test_b8_all_candidates_rejected_when_cap_exceeded(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """Verify that if all candidates violate B8 policy, all are rejected."""
    prod_expensive = _make_b6_product(
        product_id="prod_expensive",
        title="Luxury Gold Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_luxury",
                domain="target.com",
                price_amount=Decimal("89.99"),  # Exceeds per_item_cap ($60.00)
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            )
        ],
    )

    candidates = b7_comparison_service.adapt_b6_products([prod_expensive])
    comparison = b7_comparison_service.compare_and_rank(
        request=shopping_request.model_copy(update={"max_price": Decimal("100.00")}),
        candidates=candidates,
    )

    decisions = b8_decision_service.evaluate_comparison_result(
        comparison_result=comparison,
        mandate=valid_mandate,
    )

    expensive_id = comparison.ranked_candidates[0].candidate_id
    assert decisions[expensive_id].status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.PER_ITEM_CAP_EXCEEDED in decisions[expensive_id].violations


def test_b6_b7_b8_currency_mismatch_rejected(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """Verify currency mismatch is strictly rejected by B8 without silent conversions."""
    prod_eur = _make_b6_product(
        product_id="prod_eur",
        title="European Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_eur",
                domain="target.com",
                price_amount=Decimal("30.00"),
                currency="EUR",  # Mismatches mandate USD
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            )
        ],
    )

    candidates = b7_comparison_service.adapt_b6_products([prod_eur])
    comparison = b7_comparison_service.compare_and_rank(
        request=shopping_request.model_copy(update={"currency": "EUR"}),
        candidates=candidates,
    )

    decisions = b8_decision_service.evaluate_comparison_result(
        comparison_result=comparison,
        mandate=valid_mandate,  # mandate is USD
    )

    eur_id = comparison.ranked_candidates[0].candidate_id
    assert decisions[eur_id].status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.CURRENCY_MISMATCH in decisions[eur_id].violations


def test_b8_expired_mandate_blocks_all_candidates(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """Verify that an expired mandate causes B8 to reject all candidates."""
    expired_mandate = valid_mandate.model_copy(
        update={"expires_at": datetime.now(timezone.utc) - timedelta(hours=1)}
    )

    prod = _make_b6_product(
        product_id="prod_valid",
        title="Valid Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_valid",
                domain="target.com",
                price_amount=Decimal("25.00"),
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            )
        ],
    )

    candidates = b7_comparison_service.adapt_b6_products([prod])
    comparison = b7_comparison_service.compare_and_rank(
        request=shopping_request,
        candidates=candidates,
    )

    decisions = b8_decision_service.evaluate_comparison_result(
        comparison_result=comparison,
        mandate=expired_mandate,
    )

    cand_id = comparison.ranked_candidates[0].candidate_id
    assert decisions[cand_id].status == PolicyDecisionStatus.REJECTED
    assert PolicyViolationCode.MANDATE_EXPIRED in decisions[cand_id].violations


def test_b6_b7_b8_deterministic_execution(
    b7_comparison_service: ComparisonService,
    b8_decision_service: DecisionService,
    shopping_request: ShoppingRequest,
    valid_mandate: MandateSnapshot,
):
    """Verify that repeated pipeline runs yield 100% deterministic ranking and policy outcomes."""
    prod = _make_b6_product(
        product_id="prod_repeat",
        title="Reproducible Lamp",
        offers=[
            NormalizedOffer(
                offer_key="off_repeat",
                domain="target.com",
                price_amount=Decimal("30.00"),
                currency="USD",
                availability="InStock",
                condition="new",
                buy_url="https://target.com/lamp",
            )
        ],
    )

    def run_pipeline():
        candidates = b7_comparison_service.adapt_b6_products([prod])
        comparison = b7_comparison_service.compare_and_rank(
            request=shopping_request,
            candidates=candidates,
        )
        decisions = b8_decision_service.evaluate_comparison_result(
            comparison_result=comparison,
            mandate=valid_mandate,
        )
        return comparison, decisions

    comp1, dec1 = run_pipeline()
    comp2, dec2 = run_pipeline()

    cand_id = comp1.selected_candidate.candidate_id
    assert comp1.selected_candidate.candidate_id == comp2.selected_candidate.candidate_id
    assert comp1.selected_candidate.ranking_score == comp2.selected_candidate.ranking_score
    assert dec1[cand_id].status == dec2[cand_id].status
    assert dec1[cand_id].rule_results == dec2[cand_id].rule_results
