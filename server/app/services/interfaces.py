"""Typed service interfaces for Carti Backend."""

from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Protocol, Set, Tuple
import uuid
from server.app.models.candidate import Candidate
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.refund import Refund
from server.app.models.request import ShoppingRequest, RequestEvent
from server.app.schemas.mandate import MandateCreate
from server.app.schemas.request import RequestCreate


class ILifecycleManager(Protocol):
    """Protocol for authoritative state transitions, leases, and lifecycle invariants."""

    def transition(
        self,
        request: ShoppingRequest,
        target_status: str,
        error_code: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> ShoppingRequest: ...

    def acquire_lease(
        self,
        request: ShoppingRequest,
        worker_id: str,
        lease_seconds: int = 60,
    ) -> bool: ...

    def renew_lease(
        self,
        request: ShoppingRequest,
        worker_id: str,
        extension_seconds: int = 60,
    ) -> bool: ...

    def release_lease(
        self,
        request: ShoppingRequest,
        worker_id: str,
    ) -> None: ...


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
        self, request_id: uuid.UUID, since_id: Optional[int] = None, user_id: Optional[uuid.UUID] = None
    ) -> List[RequestEvent]: ...


class IAgentOrchestrator(Protocol):
    """Protocol for running background search, evaluation, and proposal generation."""

    def start_request_run(self, request_id: uuid.UUID, user_id: uuid.UUID) -> None: ...
    def stop_request_run(self, request_id: uuid.UUID) -> None: ...


class IAgentLoop(Protocol):
    """Protocol for controlled agent loop and research execution (B5)."""

    async def run(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        request_text: str,
        mandate: Optional[Mandate] = None,
        discovery_service: Optional[Any] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> Any: ...


class IToolGateway(Protocol):
    """Protocol for centralized allowlisted tool gateway (B5)."""

    def is_tool_approved(self, tool_name: str) -> bool: ...
    def is_tool_forbidden(self, tool_name: str) -> bool: ...
    async def execute_tool(
        self,
        call: Any,
        context: Any,
        execution_history: List[Any],
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> Any: ...


class ILLMProvider(Protocol):
    """Protocol for LLM provider operations (B5)."""

    async def generate_structured(
        self,
        prompt: str,
        schema_cls: Any,
        system_instruction: Optional[str] = None,
    ) -> Any: ...

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str: ...


class IDiscoveryService(Protocol):
    """Protocol for product discovery across authorized retailers (B6)."""

    def search_candidates(
        self,
        query: str,
        max_price: Optional[Decimal],
        currency: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]: ...


class IRankingService(Protocol):
    """Protocol for ranking and explaining candidates (B7)."""

    def rank_candidates(
        self,
        candidates: List[Candidate],
        query: str,
        mandate: Mandate,
    ) -> List[Candidate]: ...


class IGuardrailEngine(Protocol):
    """Protocol for deterministic purchase rule enforcement (B8)."""

    def evaluate_proposal(self, proposal: Proposal, mandate: Mandate) -> Tuple[bool, List[Dict[str, Any]]]: ...
    def evaluate_candidate(self, candidate: Candidate, mandate: Mandate, available_budget: Decimal) -> Tuple[bool, Optional[str]]: ...


class IProposalCreationService(Protocol):
    """Protocol for final proposal synthesis and retailer verification (B9)."""

    def create_proposal_from_candidate(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        mandate_id: uuid.UUID,
        candidate_id: uuid.UUID,
        offer_id: uuid.UUID,
        quantity: int,
        rationale: str,
    ) -> Proposal: ...


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
