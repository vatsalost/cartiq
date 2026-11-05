"""
Decision service for Module B8 — Deterministic Guardrail & Policy Engine.

This is the top-level public API of B8. It converts the full list of
PolicyRuleResult objects into a single authoritative, immutable PolicyDecision.

The decision algorithm:
1. If any MANDATE_MISSING rule failed → UNABLE_TO_DETERMINE (not REJECTED,
   because we could not evaluate at all — B9 must treat this as non-approvable).
2. If any mandate-structural rule failed (expired/invalid/currency missing)
   → REJECTED (mandate is definitively unusable).
3. If proposal/offer input is structurally invalid → INVALID_INPUT.
4. If any other policy rule failed → REJECTED.
5. If all rules passed → APPROVED.

LLM scores, B7 rankings, and downstream module requests CANNOT change
a decision produced by this service.
"""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from modules.b7_candidate_ranking.models import MandateSnapshot
from modules.b8_guardrail_policy.eligibility_engine import evaluate_proposal
from modules.b8_guardrail_policy.exceptions import InvalidInputError, PolicyEvaluationError
from modules.b8_guardrail_policy.models import (
    PolicyDecision,
    PolicyDecisionStatus,
    PolicyRuleResult,
    PolicyViolationCode,
    ProposalEvaluationRequest,
)

logger = logging.getLogger("cartiq.b8.decision_service")

# Violation codes that map to UNABLE_TO_DETERMINE (can't evaluate at all)
_UNABLE_TO_DETERMINE_CODES: frozenset[PolicyViolationCode] = frozenset({
    PolicyViolationCode.MANDATE_MISSING,
})

# Violation codes that map to INVALID_INPUT (bad data structure from caller)
_INVALID_INPUT_CODES: frozenset[PolicyViolationCode] = frozenset({
    PolicyViolationCode.INVALID_OFFER_DATA,
    PolicyViolationCode.INVALID_PRODUCT_DATA,
    PolicyViolationCode.INVALID_PRICE,
})


def _derive_status(rule_results: list[PolicyRuleResult]) -> PolicyDecisionStatus:
    """Deterministically map rule results to a PolicyDecisionStatus.

    Priority order (highest to lowest):
    1. UNABLE_TO_DETERMINE — mandate is missing; cannot evaluate.
    2. INVALID_INPUT       — structurally bad input data.
    3. REJECTED            — policy rule violation.
    4. APPROVED            — all rules passed.
    """
    failed_codes: set[PolicyViolationCode] = {
        r.violation_code for r in rule_results
        if not r.passed and r.violation_code is not None
    }

    if failed_codes & _UNABLE_TO_DETERMINE_CODES:
        return PolicyDecisionStatus.UNABLE_TO_DETERMINE

    if failed_codes & _INVALID_INPUT_CODES:
        return PolicyDecisionStatus.INVALID_INPUT

    if failed_codes:
        return PolicyDecisionStatus.REJECTED

    return PolicyDecisionStatus.APPROVED


class DecisionService:
    """Authoritative B8 policy decision service.

    Usage (by B9 Proposal Service):
    --------------------------------
        from modules.b8_guardrail_policy import DecisionService
        from modules.b8_guardrail_policy.models import ProposalEvaluationRequest

        svc = DecisionService()
        decision = svc.evaluate(proposal=proposal_req, mandate=mandate_snapshot)

        if not decision.is_safe_to_proceed:
            raise PolicyRejectionError(decision.rejection_reasons)

    Security contract:
    ------------------
    - B7 ranking scores (proposal.b7_ranking_score) are logged for observability
      but NEVER used to influence the decision.
    - Callers CANNOT override a REJECTED or UNABLE_TO_DETERMINE decision.
    - Decision objects are frozen (immutable) after creation.
    """

    def evaluate(
        self,
        proposal: ProposalEvaluationRequest,
        mandate: Optional[MandateSnapshot],
        now: Optional[datetime] = None,
        reference_price: Optional[Decimal] = None,
    ) -> PolicyDecision:
        """Evaluate a proposed purchase against all applicable policy rules.

        Args:
            proposal:        Typed proposal request (from B9).
            mandate:         Active mandate snapshot (from B3/B7 layer).
            now:             Current UTC time (injectable for deterministic tests).
            reference_price: Optional earlier-observed price for tolerance drift checks.

        Returns:
            Authoritative, immutable PolicyDecision.

        Raises:
            InvalidInputError:    If the proposal itself is structurally malformed.
            PolicyEvaluationError: On unexpected internal engine failures.
        """
        current_time = now or datetime.now(timezone.utc)
        decision_id = str(uuid.uuid4())

        # Log the incoming evaluation (never log sensitive mandate secrets)
        logger.info(
            "B8 policy evaluation started: decision_id=%s, candidate_id=%s, "
            "price=%s %s, quantity=%d",
            decision_id,
            proposal.candidate_id,
            proposal.price_amount,
            proposal.currency,
            proposal.quantity,
        )

        # Security note: B7 ranking score is logged for observability only.
        # It MUST NOT influence the policy decision.
        if proposal.b7_ranking_score is not None:
            logger.debug(
                "B7 ranking score %s received for candidate %s — "
                "score is IGNORED by B8 policy evaluation.",
                proposal.b7_ranking_score,
                proposal.candidate_id,
            )

        try:
            rule_results = evaluate_proposal(
                proposal=proposal,
                mandate=mandate,
                now=current_time,
                reference_price=reference_price,
            )
        except (TypeError, ValueError, AttributeError) as exc:
            logger.error(
                "Invalid input during B8 policy evaluation: decision_id=%s, error=%s",
                decision_id,
                exc,
            )
            raise InvalidInputError(
                f"Policy evaluation received structurally invalid input: {exc}"
            ) from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error in B8 policy evaluation: decision_id=%s", decision_id
            )
            raise PolicyEvaluationError(
                f"Unexpected error during policy evaluation: {exc}"
            ) from exc

        # Derive authoritative decision status deterministically.
        status = _derive_status(rule_results)

        # Collect violations and rejection reasons from failed rules.
        violations: list[PolicyViolationCode] = [
            r.violation_code
            for r in rule_results
            if not r.passed and r.violation_code is not None
        ]
        rejection_reasons: list[str] = [
            r.detail
            for r in rule_results
            if not r.passed
        ]

        decision = PolicyDecision(
            decision_id=decision_id,
            status=status,
            candidate_id=proposal.candidate_id,
            offer_key=proposal.offer_key,
            rule_results=rule_results,
            violations=violations,
            rejection_reasons=rejection_reasons,
            evaluated_price=proposal.price_amount,
            evaluated_currency=proposal.currency,
            evaluated_quantity=proposal.quantity,
            mandate_status_at_evaluation=mandate.status if mandate else None,
            evaluated_at=current_time,
        )

        logger.info(
            "B8 policy evaluation complete: decision_id=%s, status=%s, violations=%s",
            decision_id,
            status,
            [v.value for v in violations],
        )

        return decision

    def evaluate_candidate_eligibility(
        self,
        candidate_id: str,
        product_id: str,
        offer_key: str,
        product_title: str,
        category: Optional[str],
        domain: str,
        buy_url: str,
        price_amount: Decimal,
        currency: str,
        availability: str,
        condition: str,
        mandate: Optional[MandateSnapshot],
        quantity: int = 1,
        attributes: Optional[dict] = None,
        observed_at: Optional[datetime] = None,
        now: Optional[datetime] = None,
    ) -> PolicyDecision:
        """Convenience method: evaluate a candidate offer's policy eligibility.

        This wraps evaluate() with explicit field arguments, suitable for use
        when B7's RankedCandidate or CandidateOption data is available.

        Returns:
            Authoritative PolicyDecision.
        """
        proposal = ProposalEvaluationRequest(
            candidate_id=candidate_id,
            product_id=product_id,
            offer_key=offer_key,
            product_title=product_title,
            category=category,
            domain=domain,
            buy_url=buy_url,
            price_amount=price_amount,
            currency=currency,
            availability=availability,
            condition=condition,
            quantity=quantity,
            attributes=attributes or {},
            observed_at=observed_at,
            b7_ranking_score=None,  # Not used in B8 policy decisions.
        )
        return self.evaluate(proposal=proposal, mandate=mandate, now=now)
