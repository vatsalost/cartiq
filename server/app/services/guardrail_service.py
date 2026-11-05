"""Guardrail Engine (B8) implementing IGuardrailEngine protocol for deterministic policy enforcement."""

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

from server.app.models.candidate import Candidate
from server.app.models.mandate import Mandate
from server.app.models.proposal import Proposal
from server.app.services.guardrails.decision_service import DecisionService
from server.app.services.guardrails.models import (
    PolicyDecisionStatus,
    ProposalEvaluationRequest,
)
from server.app.services.interfaces import IGuardrailEngine
from server.app.services.ranking.models import MandateSnapshot

logger = logging.getLogger("carti.guardrails")


class GuardrailEngine(IGuardrailEngine):
    """Deterministic guardrail policy engine implementing IGuardrailEngine."""

    def __init__(self, decision_service: Optional[DecisionService] = None):
        self.decision_service = decision_service or DecisionService()

    def evaluate_candidate(
        self,
        candidate: Candidate,
        mandate: Mandate,
        available_budget: Decimal,
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate a single candidate against deterministic spending and policy guardrails."""
        if not candidate.offers:
            return False, "Candidate has no offers"

        offer = candidate.offers[0]

        # 1. Availability check
        if not offer.availability or offer.availability.lower() != "instock":
            return False, f"Item is unavailable ({offer.availability})"

        # 2. Currency check
        if offer.currency.upper() != mandate.currency.upper():
            return False, f"Currency mismatch: offer in {offer.currency}, mandate is {mandate.currency}"

        # 3. Per-item cap
        if mandate.per_item_cap is not None and offer.price_amount > mandate.per_item_cap:
            return False, f"Price {offer.price_amount} exceeds per-item cap of {mandate.per_item_cap}"

        # 4. Available budget ceiling
        if offer.price_amount > available_budget:
            return False, f"Price {offer.price_amount} exceeds available budget of {available_budget}"

        # 5. Allowed categories
        if mandate.allowed_categories and candidate.category:
            allowed = [c.lower() for c in mandate.allowed_categories]
            if candidate.category.lower() not in allowed:
                return False, f"Category '{candidate.category}' not in allowed categories"

        # 6. Blocked categories
        if mandate.blocked_categories and candidate.category:
            blocked = [c.lower() for c in mandate.blocked_categories]
            if candidate.category.lower() in blocked:
                return False, f"Category '{candidate.category}' is in blocked categories"

        # 7. Allowed retailers
        if mandate.allowed_retailers and offer.domain:
            allowed_ret = [r.lower() for r in mandate.allowed_retailers]
            if offer.domain.lower() not in allowed_ret:
                return False, f"Retailer '{offer.domain}' not in allowed retailers"

        return True, None

    def evaluate_proposal(
        self,
        proposal: Proposal,
        mandate: Mandate,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Evaluate a full purchase proposal against authoritative B8 policy rules."""
        mandate_snapshot = MandateSnapshot(
            total_budget=mandate.total_budget,
            currency=mandate.currency,
            per_item_cap=mandate.per_item_cap,
            allowed_categories=mandate.allowed_categories,
            blocked_categories=mandate.blocked_categories,
            allowed_retailers=mandate.allowed_retailers,
            max_quantity=mandate.max_quantity,
            price_tolerance=mandate.price_tolerance,
            status=mandate.status,
            expires_at=mandate.expires_at,
        )

        domain = ""
        category = None
        title = "Proposal Item"
        if proposal.candidate:
            title = proposal.candidate.title
            category = proposal.candidate.category
        if proposal.offer:
            domain = proposal.offer.domain

        eval_req = ProposalEvaluationRequest(
            proposal_id=str(proposal.id),
            product_id=str(proposal.candidate_id),
            product_title=title,
            offer_key=str(proposal.offer_id),
            merchant_domain=domain,
            buy_url=proposal.offer.buy_url if proposal.offer else f"https://{domain}/checkout",
            unit_price=proposal.unit_price_at_proposal,
            currency=proposal.currency,
            quantity=proposal.quantity,
            shipping_price=Decimal("0.00"),
            tax_price=Decimal("0.00"),
            total_price=proposal.subtotal_at_proposal,
            category=category,
            availability="InStock",
        )

        decision = self.decision_service.evaluate(
            proposal=eval_req,
            mandate=mandate_snapshot,
        )

        rule_results = [r.model_dump() for r in decision.rule_results]
        is_approved = decision.status == PolicyDecisionStatus.APPROVED
        return is_approved, rule_results
