"""Authoritative request lifecycle state machine and worker lease manager."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.base import utc_now
from server.app.models.request import ShoppingRequest
from server.app.schemas.request import RequestStatus

TERMINAL_STATUSES: Set[str] = {
    RequestStatus.PROPOSAL_READY.value,
    RequestStatus.NO_MATCH.value,
    RequestStatus.BLOCKED.value,
    RequestStatus.FAILED.value,
    RequestStatus.CANCELLED.value,
}

PERMITTED_TRANSITIONS: Dict[str, Set[str]] = {
    RequestStatus.QUEUED.value: {
        RequestStatus.RUNNING.value,
        RequestStatus.CANCELLED.value,
        RequestStatus.FAILED.value,
    },
    RequestStatus.RUNNING.value: {
        RequestStatus.PROPOSAL_READY.value,
        RequestStatus.NO_MATCH.value,
        RequestStatus.BLOCKED.value,
        RequestStatus.FAILED.value,
        RequestStatus.CANCELLED.value,
    },
    RequestStatus.PROPOSAL_READY.value: set(),
    RequestStatus.NO_MATCH.value: set(),
    RequestStatus.BLOCKED.value: set(),
    RequestStatus.FAILED.value: set(),
    RequestStatus.CANCELLED.value: set(),
}


def is_terminal_status(status: str) -> bool:
    """Check whether a request status represents a terminal state."""
    return status in TERMINAL_STATUSES


def can_transition(current_status: str, target_status: str) -> bool:
    """Check if state transition is structurally valid."""
    if current_status == target_status == RequestStatus.CANCELLED.value:
        return True
    return target_status in PERMITTED_TRANSITIONS.get(current_status, set())


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime object is timezone-aware in UTC for SQLite/Postgres compatibility."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class RequestLifecycleManager:
    """Centralized state machine enforcing lifecycle invariants, leases, and concurrency."""

    def __init__(self, db: Session):
        self.db = db

    def transition(
        self,
        request: ShoppingRequest,
        target_status: str,
        error_code: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> ShoppingRequest:
        """Atomically validate and execute a request state transition."""
        current_status = request.status

        # Idempotent re-cancellation
        if current_status == RequestStatus.CANCELLED.value and target_status == RequestStatus.CANCELLED.value:
            return request

        # Disallow transitions from terminal states
        if current_status in TERMINAL_STATUSES:
            if target_status == RequestStatus.CANCELLED.value:
                raise CartiAPIException(
                    code=CartiErrorCode.REQUEST_ALREADY_COMPLETED,
                    message=f"Cannot cancel request in terminal state '{current_status}'.",
                    status_code=400,
                )
            raise CartiAPIException(
                code=CartiErrorCode.INVALID_STATE_TRANSITION,
                message=f"Cannot transition terminal request from '{current_status}' to '{target_status}'.",
                status_code=400,
            )

        # Disallow invalid graph transitions
        allowed = PERMITTED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise CartiAPIException(
                code=CartiErrorCode.INVALID_STATE_TRANSITION,
                message=(
                    f"Invalid state transition: '{current_status}' -> '{target_status}'. "
                    f"Permitted next states: {sorted(list(allowed))}."
                ),
                status_code=400,
            )

        # Apply state transition
        request.status = target_status
        now = utc_now()

        if target_status == RequestStatus.RUNNING.value:
            if not request.processing_started_at:
                request.processing_started_at = now

        if target_status in TERMINAL_STATUSES:
            request.completed_at = now
            # Release any active worker lock
            request.locked_by = None
            request.locked_until = None

        if error_code is not None:
            request.error_code = error_code
        if error_details is not None:
            request.error_details = error_details

        self.db.commit()
        self.db.refresh(request)
        return request

    def acquire_lease(
        self,
        request: ShoppingRequest,
        worker_id: str,
        lease_seconds: int = 60,
    ) -> bool:
        """Acquire or renew an exclusive processing lease on a non-terminal request."""
        now = utc_now()

        # Cannot lease completed or cancelled requests
        if is_terminal_status(request.status):
            return False

        # Check existing lock
        if request.locked_by and request.locked_by != worker_id:
            locked_until = ensure_utc(request.locked_until)
            if locked_until and locked_until > now:
                # Active lock held by another worker
                return False

        # Check retry bounds
        if request.retry_count >= request.max_retries:
            return False

        request.locked_by = worker_id
        request.locked_until = now + timedelta(seconds=lease_seconds)
        request.retry_count += 1
        self.db.commit()
        self.db.refresh(request)
        return True

    def renew_lease(
        self,
        request: ShoppingRequest,
        worker_id: str,
        extension_seconds: int = 60,
    ) -> bool:
        """Extend an existing lease for long-running execution."""
        if is_terminal_status(request.status):
            return False
        if request.locked_by != worker_id:
            return False

        request.locked_until = utc_now() + timedelta(seconds=extension_seconds)
        self.db.commit()
        return True

    def release_lease(
        self,
        request: ShoppingRequest,
        worker_id: str,
    ) -> None:
        """Release worker lease upon termination or safe suspension."""
        if request.locked_by == worker_id:
            request.locked_by = None
            request.locked_until = None
            self.db.commit()
