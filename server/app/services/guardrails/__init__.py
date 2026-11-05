"""
Module B8 — Deterministic Guardrail & Policy Engine.

Public API surface for the B8 policy engine. Import from here.

Usage (B9 Proposal Service):
    from server.app.services.guardrails import (
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

from server.app.services.guardrails.decision_service import DecisionService
from server.app.services.guardrails.exceptions import (
    B8Error,
    InvalidInputError,
    MandateExpiredError,
    MandateInvalidError,
    MandateMissingError,
    PolicyEvaluationError,
)
from server.app.services.guardrails.models import (
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
