"""Request service managing natural language shopping requests, lifecycle state, and SSE logs."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.mandate import Mandate
from server.app.models.request import ShoppingRequest, RequestEvent
from server.app.schemas.request import RequestCreate, RequestEventResponse, RequestStatus
from server.app.services.agent_orchestrator import agent_orchestrator
from server.app.services.audit_service import AuditService
from server.app.services.event_bus import event_bus
from server.app.services.lifecycle import RequestLifecycleManager, is_terminal_status
from server.app.services.mandate_service import MandateService


class RequestService:
    """Manages shopping request lifecycle, state transitions, leases, and event replay."""

    def __init__(self, db: Session):
        self.db = db
        self.mandate_service = MandateService(db)
        self.audit_service = AuditService(db)
        self.lifecycle = RequestLifecycleManager(db)

    def create_request(
        self,
        user_id: uuid.UUID,
        request_in: RequestCreate,
        client_request_id: Optional[str] = None,
    ) -> ShoppingRequest:
        """Create and queue a shopping request, snapshotting current active mandate version."""
        # 1. Idempotency check: if client_request_id supplied, return existing request if found
        if client_request_id:
            existing = self.db.scalars(
                select(ShoppingRequest).where(
                    ShoppingRequest.user_id == user_id,
                    ShoppingRequest.client_request_id == client_request_id,
                )
            ).first()
            if existing:
                return existing

        # 2. Mandate validation & retrieval
        mandate = self.mandate_service.get_current_mandate(user_id)
        if not mandate:
            raise CartiAPIException(
                code=CartiErrorCode.MANDATE_NOT_FOUND,
                message="No active spending mandate found. Please create a mandate before submitting requests.",
                status_code=404,
            )

        self.mandate_service.validate_mandate_active(mandate)

        normalized_filters = (
            request_in.filters.model_dump(mode="json", exclude_none=True)
            if request_in.filters
            else {}
        )

        shopping_request = ShoppingRequest(
            user_id=user_id,
            mandate_id=mandate.id,
            client_request_id=client_request_id,
            request_text=request_in.text.strip(),
            normalized_intent=normalized_filters,
            status=RequestStatus.QUEUED.value,
            retry_count=0,
            max_retries=3,
        )
        self.db.add(shopping_request)
        self.db.commit()
        self.db.refresh(shopping_request)

        # Record synchronous start events
        self.add_request_event(
            request_id=shopping_request.id,
            event_type="request_started",
            payload={
                "request_id": str(shopping_request.id),
                "step": "request_started",
                "message": "Shopping request received and queued.",
                "progress": 5,
            },
        )

        self.add_request_event(
            request_id=shopping_request.id,
            event_type="mandate_checked",
            payload={
                "request_id": str(shopping_request.id),
                "step": "mandate_checked",
                "message": f"Verified active mandate v{mandate.version} with budget {mandate.total_budget} {mandate.currency}.",
                "progress": 10,
            },
        )

        self.audit_service.record_event(
            user_id=user_id,
            request_id=shopping_request.id,
            event_type="request_created",
            details={
                "mandate_id": str(mandate.id),
                "mandate_version": mandate.version,
                "text": shopping_request.request_text,
                "client_request_id": client_request_id,
            },
        )

        # Trigger background execution pipeline
        agent_orchestrator.start_request_run(shopping_request.id, user_id)

        return shopping_request

    def get_request(
        self, request_id: uuid.UUID, user_id: uuid.UUID
    ) -> ShoppingRequest:
        """Retrieve request and verify user ownership."""
        req = self.db.get(ShoppingRequest, request_id)
        if not req:
            raise CartiAPIException(
                code=CartiErrorCode.REQUEST_NOT_FOUND,
                message=f"Shopping request {request_id} not found.",
                status_code=404,
            )
        if req.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to view this request.",
                status_code=403,
            )
        return req

    def cancel_request(
        self, request_id: uuid.UUID, user_id: uuid.UUID
    ) -> ShoppingRequest:
        """Cancel an active shopping request."""
        req = self.get_request(request_id, user_id)

        if req.status == RequestStatus.CANCELLED.value:
            return req

        # Transition via central lifecycle manager
        self.lifecycle.transition(
            request=req,
            target_status=RequestStatus.CANCELLED.value,
        )

        # Stop background worker execution
        agent_orchestrator.stop_request_run(request_id)

        # Release any pending uncaptured budget reservations for associated proposals
        if req.proposals:
            for proposal in req.proposals:
                if proposal.order and proposal.order.budget_reserved > Decimal("0.00"):
                    # Safeguard: Never alter or reverse already completed or refunded payments
                    if proposal.order.status not in ("completed", "refunded"):
                        self.mandate_service.release_budget_reservation(
                            proposal.order.id, reason="request_cancelled"
                        )

        self.add_request_event(
            request_id=request_id,
            event_type="request_cancelled",
            payload={
                "request_id": str(request_id),
                "step": "request_cancelled",
                "message": "Shopping request was cancelled by the user.",
                "progress": 100,
            },
        )

        self.audit_service.record_event(
            user_id=user_id,
            request_id=request_id,
            event_type="request_cancelled",
            decision="cancelled",
        )
        return req

    def add_request_event(
        self, request_id: uuid.UUID, event_type: str, payload: Dict[str, Any]
    ) -> RequestEvent:
        """Add event to database and broadcast to any open SSE connections."""
        # Sanitize payload: never expose provider credentials, internal tokens, or secret keys
        sanitized_payload = self._sanitize_payload(payload)

        event = RequestEvent(
            request_id=request_id,
            event_type=event_type,
            payload=sanitized_payload,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Publish asynchronously if event loop is running
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                dto = RequestEventResponse.model_validate(event)
                loop.create_task(event_bus.publish(request_id, dto))
        except Exception:
            pass

        return event

    def get_request_events(
        self,
        request_id: uuid.UUID,
        since_id: Optional[int] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[RequestEvent]:
        """Fetch all stored events for request replay with ownership verification."""
        if user_id is not None:
            self.get_request(request_id, user_id)
        stmt = select(RequestEvent).where(RequestEvent.request_id == request_id)
        if since_id is not None:
            stmt = stmt.where(RequestEvent.id > since_id)
        stmt = stmt.order_by(RequestEvent.id.asc())
        return list(self.db.scalars(stmt).all())

    @staticmethod
    def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive internal keys from SSE event payloads."""
        redacted_keys = {
            "password",
            "password_hash",
            "secret",
            "api_key",
            "client_secret",
            "token",
            "access_token",
            "session_secret",
            "paypal_client_secret",
        }
        sanitized = {}
        for k, v in payload.items():
            if any(sensitive in k.lower() for sensitive in redacted_keys):
                continue
            if isinstance(v, dict):
                sanitized[k] = RequestService._sanitize_payload(v)
            else:
                sanitized[k] = v
        return sanitized
