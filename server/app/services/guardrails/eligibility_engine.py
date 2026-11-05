"""
Eligibility engine for Module B8 — Deterministic Guardrail & Policy Engine.

Orchestrates all individual policy rules against a validated mandate and
a proposed purchase to produce a structured list of rule results.

This module is the single point of truth for which rules are evaluated
and in what order. The decision_service uses these results to produce
the final PolicyDecision.

Design guarantees:
- Collects ALL applicable rule violations (no early-abort on first failure).
- Pure function: same inputs → same outputs.
- Zero LLM calls, zero external state.
- Cannot be overridden by B7 ranking scores.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from server.app.services.ranking.models import MandateSnapshot
from server.app.services.guardrails.mandate_validator import validate_mandate
from server.app.services.guardrails.models import (
    PolicyRuleResult,
    PolicyViolationCode,
    ProposalEvaluationRequest,
)
from server.app.services.guardrails.policy_rules import (
    rule_budget_not_exceeded,
    rule_category_allowed,
    rule_category_not_blocked,
    rule_condition_allowed,
    rule_currency_consistent,
    rule_offer_in_stock,
    rule_offer_price_valid,
    rule_per_item_cap,
    rule_price_within_tolerance,
    rule_product_data_valid,
    rule_quantity_within_limit,
    rule_required_attributes_satisfied,
    rule_retailer_allowed,
)

logger = logging.getLogger("cartiq.b8.eligibility_engine")


def evaluate_proposal(
    proposal: ProposalEvaluationRequest,
    mandate: Optional[MandateSnapshot],
    now: Optional[datetime] = None,
    reference_price: Optional[Decimal] = None,
) -> list[PolicyRuleResult]:
    """Evaluate all applicable policy rules for a proposed purchase.

    Runs mandate validation first. If the mandate is structurally invalid,
    returns those failures immediately without evaluating candidate-level rules
    (since currency/budget checks would be meaningless without a valid mandate).

    Args:
        proposal:        The proposed purchase details submitted by B9.
        mandate:         The active mandate snapshot from B3/B7.
        now:             Current UTC time (injectable for deterministic testing).
        reference_price: Optional base price for tolerance drift checks.

    Returns:
        List of PolicyRuleResult — empty only if every rule passed.
        A non-empty list must result in REJECTED or UNABLE_TO_DETERMINE by decision_service.

    Note:
        B7 ranking scores (proposal.b7_ranking_score) are EXPLICITLY IGNORED here.
        A high ranking score from B7 is never used to approve a proposal.
    """
    current_time = now or datetime.now(timezone.utc)
    all_results: list[PolicyRuleResult] = []

    # -----------------------------------------------------------------------
    # Phase 1: Mandate lifecycle validation
    # -----------------------------------------------------------------------
    mandate_results = validate_mandate(mandate=mandate, now=current_time)
    all_results.extend(mandate_results)

    mandate_failed = any(not r.passed for r in mandate_results)
    if mandate_failed:
        # Cannot safely evaluate monetary or category rules without a valid mandate.
        logger.warning(
            "Mandate validation failed (%d violations); skipping candidate-level rules.",
            sum(1 for r in mandate_results if not r.passed),
        )
        return all_results

    # mandate is not None here (validate_mandate guarantees this if no MANDATE_MISSING failure)
    assert mandate is not None  # for type checkers

    # -----------------------------------------------------------------------
    # Phase 2: Offer and product structural validity
    # -----------------------------------------------------------------------
    all_results.append(
        rule_product_data_valid(
            product_id=proposal.product_id,
            product_title=proposal.product_title,
        )
    )

    all_results.append(
        rule_offer_price_valid(
            price_amount=proposal.price_amount,
            offer_key=proposal.offer_key,
            buy_url=proposal.buy_url,
            domain=proposal.domain,
        )
    )

    # -----------------------------------------------------------------------
    # Phase 3: Stock availability
    # -----------------------------------------------------------------------
    all_results.append(rule_offer_in_stock(availability=proposal.availability))

    # -----------------------------------------------------------------------
    # Phase 4: Currency consistency
    # (Evaluated before monetary limits — mismatch makes budget checks meaningless)
    # -----------------------------------------------------------------------
    mandate_currency = mandate.currency.strip().upper()
    all_results.append(
        rule_currency_consistent(
            offer_currency=proposal.currency,
            mandate_currency=mandate_currency,
        )
    )

    # -----------------------------------------------------------------------
    # Phase 5: Spending limits
    # (Only evaluated when currencies match, to avoid nonsensical comparisons)
    # -----------------------------------------------------------------------
    currency_ok = proposal.currency.strip().upper() == mandate_currency

    all_results.append(
        rule_budget_not_exceeded(
            price_amount=proposal.price_amount,
            offer_currency=proposal.currency,
            total_budget=mandate.total_budget,
            mandate_currency=mandate_currency,
        )
    )

    all_results.append(
        rule_per_item_cap(
            price_amount=proposal.price_amount,
            offer_currency=proposal.currency,
            per_item_cap=mandate.per_item_cap,
            mandate_currency=mandate_currency,
        )
    )

    # -----------------------------------------------------------------------
    # Phase 6: Category restrictions
    # -----------------------------------------------------------------------
    all_results.append(
        rule_category_not_blocked(
            product_category=proposal.category,
            blocked_categories=mandate.blocked_categories,
        )
    )

    all_results.append(
        rule_category_allowed(
            product_category=proposal.category,
            allowed_categories=mandate.allowed_categories,
        )
    )

    # -----------------------------------------------------------------------
    # Phase 7: Retailer allowlist
    # -----------------------------------------------------------------------
    all_results.append(
        rule_retailer_allowed(
            offer_domain=proposal.domain,
            allowed_retailers=mandate.allowed_retailers,
        )
    )

    # -----------------------------------------------------------------------
    # Phase 8: Quantity restriction
    # -----------------------------------------------------------------------
    all_results.append(
        rule_quantity_within_limit(
            quantity=proposal.quantity,
            max_quantity=mandate.max_quantity,
        )
    )

    # -----------------------------------------------------------------------
    # Phase 9: Condition and Required Attributes
    # -----------------------------------------------------------------------
    all_results.append(
        rule_condition_allowed(
            offer_condition=proposal.condition,
            required_condition=proposal.required_condition,
        )
    )

    if proposal.required_attributes:
        all_results.append(
            rule_required_attributes_satisfied(
                attributes=proposal.attributes,
                required_attributes=proposal.required_attributes,
                product_title=proposal.product_title,
            )
        )

    # -----------------------------------------------------------------------
    # Phase 10: Price tolerance drift (checkout re-validation only)
    # -----------------------------------------------------------------------
    if reference_price is not None and currency_ok:
        all_results.append(
            rule_price_within_tolerance(
                price_amount=proposal.price_amount,
                reference_price=reference_price,
                price_tolerance=mandate.price_tolerance,
                currency=proposal.currency,
            )
        )

    logger.info(
        "Policy evaluation complete: %d rules evaluated, %d violations found.",
        len(all_results),
        sum(1 for r in all_results if not r.passed),
    )

    return all_results
