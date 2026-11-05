"""
Module B8 — Deterministic Guardrail & Policy Engine.

Public API surface for the B8 policy engine. Import from here.

Usage (B9 Proposal Service):
    from modules.b8_guardrail_policy import (
        DecisionService,
        ProposalEvaluationRequest,
        PolicyDecision,
        PolicyDecisionStatus,
    )

    svc = DecisionService()
    decision = svc.evaluate(proposal=req, mandate=mandate_snapshot)

    if not decision.is_safe_to_proceed:
        # Hard rejection — B9 must not proceed with checkout.
        raise SomeRejectionException(decision.rejection_reasons)
"""

from modules.b8_guardrail_policy.decision_service import DecisionService
from modules.b8_guardrail_policy.exceptions import (
    B8Error,
    InvalidInputError,
    MandateExpiredError,
    MandateInvalidError,
    MandateMissingError,
    PolicyEvaluationError,
)
from modules.b8_guardrail_policy.models import (
    PolicyDecision,
    PolicyDecisionStatus,
    PolicyRuleResult,
    PolicyViolationCode,
    ProposalEvaluationRequest,
)

__all__ = [
    # Primary service
    "DecisionService",
    # Models
    "PolicyDecision",
    "PolicyDecisionStatus",
    "PolicyRuleResult",
    "PolicyViolationCode",
    "ProposalEvaluationRequest",
    # Exceptions
    "B8Error",
    "InvalidInputError",
    "MandateExpiredError",
    "MandateInvalidError",
    "MandateMissingError",
    "PolicyEvaluationError",
]
