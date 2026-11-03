"""Typed service interfaces for Carti Backend."""

from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, List, Optional, Protocol, Tuple
import uuid
from server.app.models.candidate import Candidate
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.refund import Refund
from server.app.models.request import ShoppingRequest, RequestEvent
from server.app.schemas.mandate import MandateCreate
from server.app.schemas.request import RequestCreate


class IMandateService(Protocol):
    """Protocol for mandate storage, versioning, and policy checks."""

    def get_current_mandate(self, user_id: uuid.UUID) -> Optional[Mandate]: ...
    def create_or_update_mandate(self, user_id: uuid.UUID, mandate_in: MandateCreate) -> Mandate: ...
    def validate_mandate_active(self, mandate: Mandate) -> None: ...
    def calculate_available_budget(self, mandate_id: uuid.UUID) -> Decimal: ...


class IRequestService(Protocol):
    """Protocol for shopping request lifecycle and SSE progress tracking."""

    def create_request(self, user_id: uuid.UUID, request_in: RequestCreate) -> ShoppingRequest: ...
    def get_request(self, request_id: uuid.UUID, user_id: uuid.UUID) -> ShoppingRequest: ...
    def cancel_request(self, request_id: uuid.UUID, user_id: uuid.UUID) -> ShoppingRequest: ...
    def add_request_event(
        self, request_id: uuid.UUID, event_type: str, payload: Dict[str, Any]
    ) -> RequestEvent: ...
    def get_request_events(
        self, request_id: uuid.UUID, since_id: Optional[int] = None
    ) -> List[RequestEvent]: ...


class IAgentOrchestrator(Protocol):
    """Protocol for running background search, evaluation, and proposal generation."""

    def start_request_run(self, request_id: uuid.UUID, user_id: uuid.UUID) -> None: ...
    def stop_request_run(self, request_id: uuid.UUID) -> None: ...


class ICandidateService(Protocol):
    """Protocol for retrieving and comparing candidate offers."""

    def get_candidates_for_request(
        self, request_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Candidate]: ...


class IProposalService(Protocol):
    """Protocol for proposal retrieval and revalidation."""

    def get_proposal(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Proposal: ...
    def validate_proposal_for_checkout(self, proposal_id: uuid.UUID, user_id: uuid.UUID) -> Proposal: ...
    def mark_proposal_stale(self, proposal_id: uuid.UUID, reason: str) -> None: ...


class IGuardrailEngine(Protocol):
    """Protocol for deterministic purchase rule enforcement."""

    def evaluate_proposal(self, proposal: Proposal, mandate: Mandate) -> Tuple[bool, List[Dict[str, Any]]]: ...


class IPayPalService(Protocol):
    """Protocol for PayPal Sandbox order creation, capture, refunds, and webhook verification."""

    def create_order(
        self, proposal: Proposal, checkout_attempt_id: str
    ) -> Tuple[str, Decimal, str]: ...
    def capture_order(self, paypal_order_id: str, idempotency_key: str) -> Tuple[str, Decimal, str, datetime]: ...
    def refund_capture(
        self, capture_id: str, amount: Decimal, currency: str, idempotency_key: str
    ) -> Tuple[str, str]: ...
    def verify_webhook_signature(
        self, headers: Dict[str, str], raw_body: bytes
    ) -> bool: ...


class IAuditService(Protocol):
    """Protocol for recording non-repudiable audit events."""

    def record_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        actor: str = "system",
        request_id: Optional[uuid.UUID] = None,
        proposal_id: Optional[uuid.UUID] = None,
        order_id: Optional[uuid.UUID] = None,
        decision: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None: ...


class IWebhookService(Protocol):
    """Protocol for processing and deduplicating PayPal webhooks."""

    def process_webhook(
        self, headers: Dict[str, str], raw_body: bytes, parsed_json: Dict[str, Any]
    ) -> Tuple[bool, str]: ...
