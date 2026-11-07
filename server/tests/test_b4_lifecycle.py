"""Unit and integration tests for Request Lifecycle State Machine and Worker Leases (B4)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.mandate import Mandate
from server.app.models.request import ShoppingRequest
from server.app.models.user import User
from server.app.schemas.request import RequestStatus
from server.app.services.lifecycle import (
    PERMITTED_TRANSITIONS,
    TERMINAL_STATUSES,
    RequestLifecycleManager,
    can_transition,
    is_terminal_status,
)


@pytest.fixture
def lifecycle_request(db, active_mandate, test_user) -> ShoppingRequest:
    """Create a persistent queued shopping request for lifecycle tests."""
    req = ShoppingRequest(
        id=uuid.uuid4(),
        user_id=test_user.id,
        mandate_id=active_mandate.id,
        request_text="Find an ergonomic wireless mouse",
        status=RequestStatus.QUEUED.value,
        retry_count=0,
        max_retries=3,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def test_transition_valid_queued_to_running(db, lifecycle_request):
    """Test 1: Valid transition queued -> running records processing_started_at."""
    manager = RequestLifecycleManager(db)
    updated = manager.transition(lifecycle_request, RequestStatus.RUNNING.value)
    assert updated.status == RequestStatus.RUNNING.value
    assert updated.processing_started_at is not None
    assert updated.completed_at is None


def test_transition_valid_running_to_proposal_ready(db, lifecycle_request):
    """Test 2: Valid transition running -> proposal_ready records completed_at."""
    manager = RequestLifecycleManager(db)
    manager.transition(lifecycle_request, RequestStatus.RUNNING.value)
    updated = manager.transition(lifecycle_request, RequestStatus.PROPOSAL_READY.value)
    assert updated.status == RequestStatus.PROPOSAL_READY.value
    assert updated.completed_at is not None
    assert is_terminal_status(updated.status)


def test_transition_valid_running_to_no_match(db, lifecycle_request):
    """Test 3: Valid transition running -> no_match records terminal state and reason."""
    manager = RequestLifecycleManager(db)
    manager.transition(lifecycle_request, RequestStatus.RUNNING.value)
    updated = manager.transition(
        lifecycle_request,
        RequestStatus.NO_MATCH.value,
        error_code=CartiErrorCode.NO_ELIGIBLE_PRODUCTS,
        error_details={"reason": "0 candidates returned"},
    )
    assert updated.status == RequestStatus.NO_MATCH.value
    assert updated.error_code == CartiErrorCode.NO_ELIGIBLE_PRODUCTS
    assert updated.error_details["reason"] == "0 candidates returned"
    assert updated.completed_at is not None


def test_transition_valid_running_to_blocked(db, lifecycle_request):
    """Test 4: Valid transition running -> blocked records guardrail failure."""
    manager = RequestLifecycleManager(db)
    manager.transition(lifecycle_request, RequestStatus.RUNNING.value)
    updated = manager.transition(
        lifecycle_request,
        RequestStatus.BLOCKED.value,
        error_code=CartiErrorCode.GUARDRAIL_BLOCKED,
        error_details={"reason": "Exceeded per-item cap"},
    )
    assert updated.status == RequestStatus.BLOCKED.value
    assert updated.error_code == CartiErrorCode.GUARDRAIL_BLOCKED
    assert updated.completed_at is not None


def test_transition_valid_running_to_failed(db, lifecycle_request):
    """Test 5: Valid transition running -> failed records error diagnostics."""
    manager = RequestLifecycleManager(db)
    manager.transition(lifecycle_request, RequestStatus.RUNNING.value)
    updated = manager.transition(
        lifecycle_request,
        RequestStatus.FAILED.value,
        error_code=CartiErrorCode.AGENT_TIMEOUT,
        error_details={"step": "search", "timeout_sec": 30},
    )
    assert updated.status == RequestStatus.FAILED.value
    assert updated.error_code == CartiErrorCode.AGENT_TIMEOUT
    assert updated.completed_at is not None


def test_transition_queued_directly_to_cancelled(db, lifecycle_request):
    """Test 6: Valid transition queued -> cancelled (cancellation before run)."""
    manager = RequestLifecycleManager(db)
    updated = manager.transition(lifecycle_request, RequestStatus.CANCELLED.value)
    assert updated.status == RequestStatus.CANCELLED.value
    assert updated.completed_at is not None


def test_transition_invalid_queued_to_proposal_ready(db, lifecycle_request):
    """Test 7: Direct transition queued -> proposal_ready is rejected."""
    manager = RequestLifecycleManager(db)
    with pytest.raises(CartiAPIException) as exc_info:
        manager.transition(lifecycle_request, RequestStatus.PROPOSAL_READY.value)
    assert exc_info.value.code == CartiErrorCode.INVALID_STATE_TRANSITION
    assert exc_info.value.status_code == 400


def test_transition_invalid_backwards_running_to_queued(db, lifecycle_request):
    """Test 8: Backwards transition running -> queued is rejected."""
    manager = RequestLifecycleManager(db)
    manager.transition(lifecycle_request, RequestStatus.RUNNING.value)
    with pytest.raises(CartiAPIException) as exc_info:
        manager.transition(lifecycle_request, RequestStatus.QUEUED.value)
    assert exc_info.value.code == CartiErrorCode.INVALID_STATE_TRANSITION


def test_transition_terminal_states_cannot_be_reopened(db, lifecycle_request):
    """Test 9: All terminal states cannot transition to any other state."""
    manager = RequestLifecycleManager(db)
    terminal_test_states = [
        RequestStatus.PROPOSAL_READY.value,
        RequestStatus.NO_MATCH.value,
        RequestStatus.BLOCKED.value,
        RequestStatus.FAILED.value,
    ]

    for term_status in terminal_test_states:
        # Create fresh request in running state
        req = ShoppingRequest(
            id=uuid.uuid4(),
            user_id=lifecycle_request.user_id,
            mandate_id=lifecycle_request.mandate_id,
            request_text="Terminal test",
            status=RequestStatus.RUNNING.value,
        )
        db.add(req)
        db.commit()

        # Move to terminal
        manager.transition(req, term_status)

        # Attempt to reopen into running
        with pytest.raises(CartiAPIException) as exc_info:
            manager.transition(req, RequestStatus.RUNNING.value)
        assert exc_info.value.code == CartiErrorCode.INVALID_STATE_TRANSITION

        # Attempt to cancel completed
        with pytest.raises(CartiAPIException) as exc_info2:
            manager.transition(req, RequestStatus.CANCELLED.value)
        assert exc_info2.value.code == CartiErrorCode.REQUEST_ALREADY_COMPLETED


def test_transition_cancellation_is_idempotent(db, lifecycle_request):
    """Test 10: Repeated cancellation on already cancelled request returns cleanly."""
    manager = RequestLifecycleManager(db)
    manager.transition(lifecycle_request, RequestStatus.CANCELLED.value)
    assert lifecycle_request.status == RequestStatus.CANCELLED.value

    # Second cancellation call should succeed idempotently
    second = manager.transition(lifecycle_request, RequestStatus.CANCELLED.value)
    assert second.status == RequestStatus.CANCELLED.value


def test_worker_lease_acquisition_and_release(db, lifecycle_request):
    """Test 11: Worker lease acquisition locks request and release frees it."""
    manager = RequestLifecycleManager(db)
    worker_a = "worker_alpha"
    worker_b = "worker_beta"

    # Worker A acquires lease
    acquired = manager.acquire_lease(lifecycle_request, worker_id=worker_a, lease_seconds=60)
    assert acquired is True
    assert lifecycle_request.locked_by == worker_a
    assert lifecycle_request.locked_until is not None
    assert lifecycle_request.retry_count == 1

    # Worker B attempts to acquire while active lease held
    conflict = manager.acquire_lease(lifecycle_request, worker_id=worker_b, lease_seconds=60)
    assert conflict is False
    assert lifecycle_request.locked_by == worker_a

    # Worker A releases lease
    manager.release_lease(lifecycle_request, worker_id=worker_a)
    assert lifecycle_request.locked_by is None
    assert lifecycle_request.locked_until is None

    # Worker B can now acquire lease
    acquired_b = manager.acquire_lease(lifecycle_request, worker_id=worker_b, lease_seconds=60)
    assert acquired_b is True
    assert lifecycle_request.locked_by == worker_b
    assert lifecycle_request.retry_count == 2


def test_worker_lease_stale_recovery(db, lifecycle_request):
    """Test 12: Expired worker lease allows recovery by another worker."""
    manager = RequestLifecycleManager(db)
    worker_old = "worker_dead"
    worker_new = "worker_recovery"

    # Simulate expired lease from a crashed worker
    lifecycle_request.locked_by = worker_old
    lifecycle_request.locked_until = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.commit()

    # Recovery worker attempts lease
    acquired = manager.acquire_lease(lifecycle_request, worker_id=worker_new, lease_seconds=60)
    assert acquired is True
    assert lifecycle_request.locked_by == worker_new


def test_worker_lease_retry_limit_exceeded(db, lifecycle_request):
    """Test 13: Exceeding max retries prevents lease acquisition."""
    manager = RequestLifecycleManager(db)
    lifecycle_request.retry_count = 3
    lifecycle_request.max_retries = 3
    db.commit()

    acquired = manager.acquire_lease(lifecycle_request, worker_id="worker_x", lease_seconds=60)
    assert acquired is False
