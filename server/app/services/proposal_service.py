"""Proposal service for proposal inspection and revalidation."""

from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.proposal import Proposal
from server.app.services.audit_service import AuditService


class ProposalService:
    """Manages purchase proposals and their checkout eligibility."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

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
            self.db.commit()

        return proposal

    def validate_proposal_for_checkout(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID
    ) -> Proposal:
        """Validate proposal state before proceeding with PayPal order creation."""
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

    def mark_proposal_stale(self, proposal_id: uuid.UUID, reason: str) -> None:
        """Mark proposal as stale when external price or stock changes."""
        proposal = self.db.get(Proposal, proposal_id)
        if proposal:
            proposal.status = "stale"
            self.db.commit()
            self.audit_service.record_event(
                user_id=proposal.user_id,
                proposal_id=proposal.id,
                event_type="proposal_marked_stale",
                reason=reason,
            )
