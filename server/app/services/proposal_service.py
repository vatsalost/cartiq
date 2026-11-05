"""Proposal service for proposal creation, inspection, lifecycle, and checkout preparation."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.base import utc_now
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest
from server.app.schemas.proposal import CheckoutPreparationResult
from server.app.services.audit_service import AuditService
from server.app.services.kernel_service import kernel_verification_service
from server.app.services.mandate_service import MandateService

logger = logging.getLogger("carti.proposals")


class ProposalService:
    """Authoritative business logic for purchase proposals and retailer verification."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.mandate_service = MandateService(db)
        self.kernel_service = kernel_verification_service

    def create_proposal(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        offer_id: Optional[uuid.UUID] = None,
        quantity: int = 1,
        rationale: Optional[str] = None,
        shipping_amount: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        mandate_id: Optional[uuid.UUID] = None,
        guardrail_result: Optional[Dict[str, Any]] = None,
        verification_result: Optional[Dict[str, Any]] = None,
        bypass_guardrails: bool = False,
    ) -> Proposal:
        """
        Create an immutable proposal snapshot after candidate selection and guardrails pass.
        Calculates subtotal, shipping, tax, and total using trusted backend data only.
        """
        # 1. Ownership & request retrieval
        request = self.db.get(ShoppingRequest, request_id)
        if not request:
            raise CartiAPIException(
                code=CartiErrorCode.REQUEST_NOT_FOUND,
                message=f"Request {request_id} not found.",
                status_code=404,
            )
        if request.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to create a proposal for this request.",
                status_code=403,
            )
        if request.status in ["cancelled", "completed", "failed"]:
            err_code = CartiErrorCode.REQUEST_CANCELLED if request.status == "cancelled" else CartiErrorCode.INVALID_REQUEST
            raise CartiAPIException(
                code=err_code,
                message=f"Cannot create proposal for request in state '{request.status}'.",
                status_code=400,
            )

        # 2. Candidate retrieval and validation
        candidate = self.db.get(Candidate, candidate_id)
        if not candidate:
            raise CartiAPIException(
                code=CartiErrorCode.INVALID_REQUEST,
                message=f"Candidate {candidate_id} not found.",
                status_code=404,
            )
        if candidate.request_id != request.id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Candidate does not belong to the specified request.",
                status_code=403,
            )

        # 3. Retailer offer retrieval and verification
        if offer_id:
            offer = self.db.get(CandidateOffer, offer_id)
        elif candidate.offers:
            offer = candidate.offers[0]
        else:
            offer = None

        if not offer or offer.candidate_id != candidate.id:
            raise CartiAPIException(
                code=CartiErrorCode.INVALID_REQUEST,
                message="Selected offer does not belong to this candidate.",
                status_code=400,
            )
        if not offer.is_eligible:
            raise CartiAPIException(
                code=CartiErrorCode.GUARDRAIL_VIOLATION,
                message="Selected retailer offer is marked ineligible.",
                status_code=400,
            )
        if offer.availability and offer.availability.lower() in ["outofstock", "out_of_stock", "soldout", "unavailable"]:
            raise CartiAPIException(
                code=CartiErrorCode.GUARDRAIL_VIOLATION,
                message="Selected retailer offer is currently out of stock.",
                status_code=400,
            )

        # 4. Mandate retrieval and active check
        target_mandate_id = mandate_id or request.mandate_id
        if not target_mandate_id:
            raise CartiAPIException(
                code=CartiErrorCode.MANDATE_NOT_FOUND,
                message="No mandate associated with this shopping request.",
                status_code=404,
            )
        mandate = self.mandate_service.get_mandate_by_id(target_mandate_id, user_id=user_id)
        self.mandate_service.validate_mandate_is_active(mandate)

        # 5. Deterministic Guardrail enforcement (B8)
        if not bypass_guardrails:
            # Quantity limit check
            if quantity < 1:
                raise CartiAPIException(
                    code=CartiErrorCode.VALIDATION_ERROR,
                    message="Proposal quantity must be at least 1.",
                    status_code=422,
                )
            if mandate.max_quantity_per_product and quantity > mandate.max_quantity_per_product:
                raise CartiAPIException(
                    code=CartiErrorCode.GUARDRAIL_VIOLATION,
                    message=f"Requested quantity ({quantity}) exceeds mandate limit ({mandate.max_quantity_per_product}).",
                    status_code=400,
                )

            # Category restriction check
            if mandate.blocked_categories and candidate.category in mandate.blocked_categories:
                raise CartiAPIException(
                    code=CartiErrorCode.GUARDRAIL_VIOLATION,
                    message=f"Product category '{candidate.category}' is blocked by mandate.",
                    status_code=400,
                )
            if mandate.allowed_categories and candidate.category not in mandate.allowed_categories:
                raise CartiAPIException(
                    code=CartiErrorCode.GUARDRAIL_VIOLATION,
                    message=f"Product category '{candidate.category}' is not in allowed mandate categories.",
                    status_code=400,
                )

            # Retailer domain check
            if mandate.allowed_retailers and offer.domain not in mandate.allowed_retailers:
                raise CartiAPIException(
                    code=CartiErrorCode.GUARDRAIL_VIOLATION,
                    message=f"Retailer '{offer.domain}' is not in allowed mandate retailers.",
                    status_code=400,
                )

            # Currency consistency check
            if offer.currency.upper() != mandate.currency.upper():
                raise CartiAPIException(
                    code=CartiErrorCode.CURRENCY_MISMATCH,
                    message=f"Offer currency '{offer.currency}' does not match mandate currency '{mandate.currency}'.",
                    status_code=400,
                )

            # Per-item cap check
            unit_price = Decimal(str(offer.price_amount))
            if unit_price > mandate.per_item_cap:
                raise CartiAPIException(
                    code=CartiErrorCode.GUARDRAIL_VIOLATION,
                    message=f"Unit price ({unit_price} {offer.currency}) exceeds mandate per-item cap ({mandate.per_item_cap} {mandate.currency}).",
                    status_code=400,
                )

        unit_price = Decimal(str(offer.price_amount))
        subtotal = unit_price * Decimal(quantity)
        shipping = Decimal(str(shipping_amount))
        tax = Decimal(str(tax_amount))
        total = subtotal + shipping + tax

        # 6. Budget availability check with row-level lock
        breakdown = self.mandate_service.calculate_available_budget(mandate.id, lock_row=True)
        if total > breakdown.available_budget:
            self.audit_service.record_event(
                user_id=user_id,
                request_id=request.id,
                event_type="budget_limit_exceeded",
                decision="rejected",
                reason=f"Proposal total ({total} {mandate.currency}) exceeds remaining available budget ({breakdown.available_budget} {mandate.currency}).",
            )
            raise CartiAPIException(
                code=CartiErrorCode.BUDGET_EXCEEDED,
                message=f"Proposal total ({total} {mandate.currency}) exceeds remaining available budget ({breakdown.available_budget} {mandate.currency}).",
                status_code=400,
            )

        # 7. Retailer verification via KERNEL (or pass-through)
        if verification_result is not None:
            verification_data = verification_result
            verification_status = verification_data.get("status", "verified")
        else:
            kernel_res = self.kernel_service.verify_retailer_offer(
                offer_url=offer.buy_url,
                expected_domain=offer.domain,
                expected_price=unit_price,
                expected_currency=offer.currency,
                expected_availability=offer.availability,
            )
            if kernel_res.status == "mismatch":
                raise CartiAPIException(
                    code=CartiErrorCode.PROPOSAL_STALE,
                    message=f"Retailer verification mismatch: {kernel_res.reason}",
                    status_code=409,
                    retryable=True,
                )
            verification_data = kernel_res.to_dict()
            verification_status = kernel_res.status

        # 8. Idempotency check: Reuse existing active proposal if identical
        existing_proposal = self.db.scalars(
            select(Proposal).where(
                Proposal.request_id == request.id,
                Proposal.candidate_id == candidate.id,
                Proposal.offer_id == offer.id,
                Proposal.status == "pending",
            )
        ).first()
        if existing_proposal:
            return existing_proposal

        # 9. Immutable snapshots
        product_snapshot = {
            "product_id": candidate.provider_product_id,
            "title": candidate.title,
            "brand": candidate.brand,
            "category": candidate.category,
            "image_url": candidate.image_url,
            "attributes": candidate.attributes,
        }
        offer_snapshot = {
            "offer_id": str(offer.id),
            "provider_offer_id": offer.provider_offer_id,
            "domain": offer.domain,
            "buy_url": offer.buy_url,
            "price_amount": str(offer.price_amount),
            "currency": offer.currency,
            "availability": offer.availability,
            "condition": offer.condition,
        }

        # 10. Persist Proposal
        now = utc_now()
        proposal = Proposal(
            request_id=request.id,
            user_id=user_id,
            mandate_id=mandate.id,
            mandate_version=mandate.version,
            candidate_id=candidate.id,
            offer_id=offer.id,
            quantity=quantity,
            unit_price_at_proposal=unit_price,
            subtotal_at_proposal=subtotal,
            shipping_amount=shipping,
            tax_amount=tax,
            total_amount=total,
            currency=offer.currency,
            rationale=rationale or candidate.rank_reason or "Selected matching candidate adhering to mandate spending policy.",
            guardrail_result=guardrail_result or {
                "passed": True,
                "checks": [
                    {"rule": "per_item_cap", "passed": True, "limit": str(mandate.per_item_cap), "actual": str(unit_price)},
                    {"rule": "total_budget", "passed": True, "limit": str(mandate.total_budget), "actual": str(total)},
                    {"rule": "allowed_categories", "passed": True},
                    {"rule": "allowed_retailers", "passed": True},
                ],
            },
            verification_result=verification_data,
            verification_status=verification_status,
            product_snapshot=product_snapshot,
            offer_snapshot=offer_snapshot,
            status="pending",
            expires_at=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )

        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)

        self.audit_service.record_event(
            user_id=user_id,
            request_id=request.id,
            proposal_id=proposal.id,
            event_type="proposal_created",
            details={
                "amount": str(proposal.total_amount),
                "currency": proposal.currency,
                "mandate_version": proposal.mandate_version,
                "retailer_domain": offer.domain,
            },
        )
        return proposal

    def create_proposal_from_candidate(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        mandate_id: uuid.UUID,
        candidate_id: uuid.UUID,
        offer_id: uuid.UUID,
        quantity: int = 1,
        rationale: Optional[str] = None,
    ) -> Proposal:
        """Adapter method satisfying IProposalCreationService protocol."""
        return self.create_proposal(
            request_id=request_id,
            user_id=user_id,
            candidate_id=candidate_id,
            offer_id=offer_id,
            quantity=quantity,
            rationale=rationale,
            mandate_id=mandate_id,
        )

    def get_proposal(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Proposal:
        """Fetch proposal ensuring caller ownership and checking expiration."""
        proposal = self.db.get(Proposal, proposal_id)
        if not proposal:
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_NOT_FOUND,
                message=f"Proposal {proposal_id} not found.",
                status_code=404,
            )

        if proposal.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to view this proposal.",
                status_code=403,
            )

        # Cross-resource ownership verification
        if proposal.request and proposal.request.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Access denied: Associated request ownership mismatch.",
                status_code=403,
            )
        if proposal.mandate and proposal.mandate.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Access denied: Associated mandate ownership mismatch.",
                status_code=403,
            )
        if proposal.candidate and proposal.candidate.request_id != proposal.request_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Access denied: Associated candidate ownership mismatch.",
                status_code=403,
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = proposal.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now and proposal.status == "pending":
            proposal.status = "expired"
            proposal.updated_at = utc_now()
            self.db.commit()
            self.audit_service.record_event(
                user_id=proposal.user_id,
                proposal_id=proposal.id,
                event_type="proposal_expired",
                reason="Proposal validity period expired.",
            )

        return proposal

    def get_proposals_for_request(self, request_id: uuid.UUID, user_id: uuid.UUID) -> List[Proposal]:
        """Fetch all proposals associated with a request for the authenticated user."""
        request = self.db.get(ShoppingRequest, request_id)
        if not request:
            raise CartiAPIException(
                code=CartiErrorCode.REQUEST_NOT_FOUND,
                message=f"Request {request_id} not found.",
                status_code=404,
            )
        if request.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to view proposals for this request.",
                status_code=403,
            )

        stmt = select(Proposal).where(Proposal.request_id == request_id).order_by(Proposal.created_at.desc())
        proposals = self.db.scalars(stmt).all()

        # Check expiry on results
        now = datetime.now(timezone.utc)
        modified = False
        for p in proposals:
            exp = p.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp <= now and p.status == "pending":
                p.status = "expired"
                p.updated_at = utc_now()
                modified = True
        if modified:
            self.db.commit()

        return proposals

    def reject_proposal(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID, reason: str = "user_rejected"
    ) -> Proposal:
        """Reject proposal, releasing any active order budget reservation."""
        proposal = self.get_proposal(proposal_id, user_id)

        if proposal.status in ["ordered", "completed"]:
            raise CartiAPIException(
                code=CartiErrorCode.INVALID_REQUEST,
                message=f"Cannot reject proposal in terminal state '{proposal.status}'.",
                status_code=400,
            )

        proposal.status = "rejected"
        proposal.updated_at = utc_now()

        # Release any in-flight order budget reservation
        if proposal.order and proposal.order.budget_reserved > Decimal("0.00"):
            self.mandate_service.release_budget_reservation(
                order_id=proposal.order.id, reason=f"proposal_rejected: {reason}"
            )

        self.db.commit()
        self.audit_service.record_event(
            user_id=user_id,
            proposal_id=proposal.id,
            event_type="proposal_rejected",
            reason=reason,
        )
        return proposal

    def expire_proposal(self, proposal_id: uuid.UUID) -> Proposal:
        """Explicitly expire a proposal and release associated reservations."""
        proposal = self.db.get(Proposal, proposal_id)
        if not proposal:
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_NOT_FOUND,
                message=f"Proposal {proposal_id} not found.",
                status_code=404,
            )

        if proposal.status not in ["ordered", "completed"]:
            proposal.status = "expired"
            proposal.updated_at = utc_now()
            if proposal.order and proposal.order.budget_reserved > Decimal("0.00"):
                self.mandate_service.release_budget_reservation(
                    order_id=proposal.order.id, reason="proposal_expired"
                )
            self.db.commit()
            self.audit_service.record_event(
                user_id=proposal.user_id,
                proposal_id=proposal.id,
                event_type="proposal_expired",
                reason="Proposal manually expired.",
            )
        return proposal

    def expire_old_proposals(self) -> int:
        """Batch sweep for expired proposals across the database."""
        now = datetime.now(timezone.utc)
        stmt = select(Proposal).where(Proposal.status == "pending", Proposal.expires_at <= now)
        expired_list = self.db.scalars(stmt).all()
        count = 0
        for p in expired_list:
            p.status = "expired"
            p.updated_at = utc_now()
            if p.order and p.order.budget_reserved > Decimal("0.00"):
                self.mandate_service.release_budget_reservation(
                    order_id=p.order.id, reason="proposal_expired_batch"
                )
            self.audit_service.record_event(
                user_id=p.user_id,
                proposal_id=p.id,
                event_type="proposal_expired",
                reason="Proposal expired in batch sweep.",
            )
            count += 1
        if count > 0:
            self.db.commit()
        return count

    def mark_proposal_stale(self, proposal_id: uuid.UUID, reason: str) -> Proposal:
        """Mark proposal as stale when external price or stock changes."""
        proposal = self.db.get(Proposal, proposal_id)
        if proposal:
            proposal.status = "stale"
            proposal.updated_at = utc_now()
            if proposal.order and proposal.order.budget_reserved > Decimal("0.00"):
                self.mandate_service.release_budget_reservation(
                    order_id=proposal.order.id, reason=f"proposal_stale: {reason}"
                )
            self.db.commit()
            self.audit_service.record_event(
                user_id=proposal.user_id,
                proposal_id=proposal.id,
                event_type="proposal_marked_stale",
                reason=reason,
            )
        return proposal

    def invalidate_proposal(self, proposal_id: uuid.UUID, reason: str) -> Proposal:
        """Invalidate proposal due to policy violation, out-of-stock, or mandate revocation."""
        proposal = self.db.get(Proposal, proposal_id)
        if proposal:
            proposal.status = "invalidated"
            proposal.updated_at = utc_now()
            if proposal.order and proposal.order.budget_reserved > Decimal("0.00"):
                self.mandate_service.release_budget_reservation(
                    order_id=proposal.order.id, reason=f"proposal_invalidated: {reason}"
                )
            self.db.commit()
            self.audit_service.record_event(
                user_id=proposal.user_id,
                proposal_id=proposal.id,
                event_type="proposal_invalidated",
                reason=reason,
            )
        return proposal

    def prepare_proposal_for_checkout(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> CheckoutPreparationResult:
        """
        Validate proposal facts, enforce current mandate, recheck budget,
        and return trusted context to B10 PayPal payment service.
        """
        proposal = self.get_proposal(proposal_id, user_id)

        # 1. State check
        if proposal.status == "expired":
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_EXPIRED,
                message="Proposal has expired and cannot proceed to checkout.",
                status_code=409,
            )
        if proposal.status != "pending":
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_STALE,
                message=f"Proposal is in state '{proposal.status}' and cannot proceed to checkout.",
                status_code=409,
                retryable=True,
            )

        # 2. Expiration check
        now = datetime.now(timezone.utc)
        exp = proposal.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp <= now:
            proposal.status = "expired"
            proposal.updated_at = utc_now()
            self.db.commit()
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_EXPIRED,
                message="Proposal has expired and cannot be checked out.",
                status_code=409,
            )

        # 3. Mandate validity check
        mandate = self.mandate_service.get_mandate_by_id(proposal.mandate_id, user_id=user_id)
        self.mandate_service.validate_mandate_is_active(mandate)

        # 4. Currency check
        if proposal.currency.upper() != mandate.currency.upper():
            raise CartiAPIException(
                code=CartiErrorCode.CURRENCY_MISMATCH,
                message=f"Proposal currency ({proposal.currency}) does not match mandate currency ({mandate.currency}).",
                status_code=400,
            )

        # 5. Offer availability check
        if proposal.offer:
            if not proposal.offer.is_eligible or (
                proposal.offer.availability
                and proposal.offer.availability.lower() in ["outofstock", "out_of_stock", "soldout", "unavailable"]
            ):
                self.mark_proposal_stale(proposal.id, "Offer is out of stock or marked ineligible.")
                raise CartiAPIException(
                    code=CartiErrorCode.PROPOSAL_STALE,
                    message="Retailer offer is no longer available or in stock.",
                    status_code=409,
                )

            # Price tolerance check
            current_price = Decimal(str(proposal.offer.price_amount))
            original_price = Decimal(str(proposal.unit_price_at_proposal))
            tolerance = getattr(mandate, "price_tolerance_pct", Decimal("0.05")) or Decimal("0.05")
            max_allowed = original_price * (Decimal("1.00") + tolerance)
            if current_price > max_allowed:
                self.mark_proposal_stale(
                    proposal.id,
                    f"Offer price increased from {original_price} to {current_price}, exceeding {tolerance * 100}% tolerance.",
                )
                raise CartiAPIException(
                    code=CartiErrorCode.PROPOSAL_STALE,
                    message=f"Offer price increased from {original_price} to {current_price}, exceeding allowed price tolerance.",
                    status_code=409,
                )

        # 6. Budget availability with row-level lock
        amount = getattr(proposal, "total_amount", proposal.subtotal_at_proposal)
        breakdown = self.mandate_service.calculate_available_budget(proposal.mandate_id, lock_row=True)
        if amount > breakdown.available_budget:
            self.audit_service.record_event(
                user_id=user_id,
                proposal_id=proposal.id,
                event_type="budget_limit_exceeded",
                decision="rejected",
                reason=f"Checkout amount ({amount} {proposal.currency}) exceeds available budget ({breakdown.available_budget} {proposal.currency}).",
            )
            raise CartiAPIException(
                code=CartiErrorCode.BUDGET_EXCEEDED,
                message=f"Checkout amount ({amount} {proposal.currency}) exceeds available budget ({breakdown.available_budget} {proposal.currency}).",
                status_code=400,
            )

        self.audit_service.record_event(
            user_id=user_id,
            proposal_id=proposal.id,
            event_type="checkout_prepared",
            details={
                "amount": str(amount),
                "currency": proposal.currency,
                "mandate_id": str(mandate.id),
                "mandate_version": mandate.version,
            },
        )

        return CheckoutPreparationResult(
            proposal_id=proposal.id,
            user_id=user_id,
            mandate_id=mandate.id,
            mandate_version=mandate.version,
            amount=amount,
            currency=proposal.currency,
            is_eligible=True,
            offer_domain=proposal.offer.domain if proposal.offer else "unknown",
            product_title=proposal.candidate.title if proposal.candidate else "Proposed Product",
            available_budget_remaining=breakdown.available_budget,
        )

    def validate_proposal_for_checkout(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        """Validate proposal state before proceeding with PayPal order creation (B10 compatibility)."""
        proposal = self.get_proposal(proposal_id, user_id)

        if proposal.status != "pending":
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_STALE,
                message=f"Proposal is in state '{proposal.status}' and cannot be ordered. A new proposal is required.",
                status_code=409,
                retryable=True,
                details={"proposal_id": str(proposal_id), "status": proposal.status},
            )

        return proposal

    def revalidate_proposal(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Proposal:
        """Revalidate proposal facts against latest mandate and offer conditions."""
        proposal = self.get_proposal(proposal_id, user_id)
        # Check mandate
        mandate = self.mandate_service.get_mandate_by_id(proposal.mandate_id, user_id=user_id)
        self.mandate_service.validate_mandate_is_active(mandate)

        # Check offer
        if proposal.offer:
            if not proposal.offer.is_eligible or (
                proposal.offer.availability
                and proposal.offer.availability.lower() in ["outofstock", "out_of_stock", "soldout"]
            ):
                self.mark_proposal_stale(proposal.id, "Retailer offer out of stock or ineligible.")
                raise CartiAPIException(
                    code=CartiErrorCode.PROPOSAL_STALE,
                    message="Retailer offer is no longer in stock or eligible.",
                    status_code=409,
                )

        return proposal
