"""Comprehensive integration and security tests for B4 Request Lifecycle and Orchestration."""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import uuid
import pytest
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest, RequestEvent
from server.app.schemas.request import RequestStatus
from server.app.services.agent_orchestrator import AgentOrchestrator
from server.app.services.request_service import RequestService


class MockDiscoveryService:
    """Mock discovery service for controllable candidate search results."""

    def __init__(self, items=None):
        self.items = items if items is not None else []

    def search_candidates(self, query, max_price, currency, filters=None):
        return self.items


@pytest.mark.anyio
async def test_request_initialization_snapshots_mandate_version(client, db, active_mandate, test_user):
    """Test 1: Request creation accurately snapshots active mandate ID and version."""
    payload = {
        "text": "Find a noise cancelling wireless keyboard",
        "filters": {"category": "Electronics", "max_price": "75.00", "currency": "USD"},
    }
    res = client.post("/api/requests", json=payload)
    assert res.status_code == 202
    data = res.json()
    req_id = uuid.UUID(data["request_id"])
    assert data["status"] == "queued"
    assert data["stream_url"] == f"/api/requests/{req_id}/stream"

    # Verify database record
    req = db.get(ShoppingRequest, req_id)
    assert req is not None
    assert req.mandate_id == active_mandate.id
    assert req.status in ("queued", "no_match")
    assert req.max_retries == 3

    # Verify synchronous start events were created
    events = db.query(RequestEvent).filter_by(request_id=req_id).order_by(RequestEvent.id.asc()).all()
    assert len(events) >= 2
    assert events[0].event_type == "request_started"
    assert events[1].event_type == "mandate_checked"
    assert f"v{active_mandate.version}" in events[1].payload["message"]


@pytest.mark.anyio
async def test_mandate_version_snapshot_invariance(client, db, active_mandate, test_user):
    """Test 2: Request retains original mandate version even if mandate is subsequently updated."""
    # Create request under mandate version 1
    res = client.post("/api/requests", json={"text": "Buy a mechanical keyboard"})
    assert res.status_code == 202
    req_id = res.json()["request_id"]

    # Now user updates mandate to version 2 with a higher budget
    from server.app.schemas.mandate import MandateCreate
    from server.app.services.mandate_service import MandateService

    mandate_svc = MandateService(db)
    new_mandate = mandate_svc.create_or_update_mandate(
        user_id=test_user.id,
        mandate_in=MandateCreate(
            total_budget=Decimal("500.00"),
            per_item_cap=Decimal("150.00"),
            currency="USD",
            allowed_categories=["Electronics", "Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=60),
        ),
    )
    assert new_mandate.version == 2

    # Verify the initial request still points to version 1 mandate
    req_res = client.get(f"/api/requests/{req_id}")
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert req_data["mandate_id"] == str(active_mandate.id)
    assert req_data["mandate_version"] == 1


def test_request_creation_rejected_when_mandate_expired(client, db, test_user):
    """Test 3: Request creation is rejected with 404 when active mandate is expired."""
    expired_mandate = Mandate(
        user_id=test_user.id,
        version=1,
        total_budget=Decimal("100.00"),
        per_item_cap=Decimal("50.00"),
        currency="USD",
        allowed_categories=["Electronics"],
        status="active",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(expired_mandate)
    db.commit()

    res = client.post("/api/requests", json={"text": "Find a wireless mouse"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == CartiErrorCode.MANDATE_NOT_FOUND


def test_request_creation_rejected_when_mandate_revoked(client, db, test_user):
    """Test 4: Request creation is rejected with 404 when mandate is revoked."""
    revoked_mandate = Mandate(
        user_id=test_user.id,
        version=1,
        total_budget=Decimal("100.00"),
        per_item_cap=Decimal("50.00"),
        currency="USD",
        allowed_categories=["Electronics"],
        status="revoked",
        expires_at=datetime.now(timezone.utc) + timedelta(days=10),
    )
    db.add(revoked_mandate)
    db.commit()

    res = client.post("/api/requests", json={"text": "Find a wireless mouse"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == CartiErrorCode.MANDATE_NOT_FOUND


@pytest.mark.anyio
async def test_orchestration_pipeline_happy_path(db, active_mandate, test_user):
    """Test 5: Pipeline coordinates discovery, guardrails, proposal creation and terminal event."""
    req_svc = RequestService(db)
    req = req_svc.create_request(
        user_id=test_user.id,
        request_in=type("Payload", (), {
            "text": "Ergonomic vertical mouse",
            "filters": None,
        })(),
    )

    # Inject discovery service returning an eligible product
    mock_discovery = MockDiscoveryService([
        {
            "product_id": "ch3_mouse_1",
            "title": "Logitech MX Master 3S",
            "category": "Electronics",
            "price": "45.00",
            "domain": "target.com",
            "buy_url": "https://target.com/item1",
            "availability": "InStock",
            "condition": "new",
            "score": "0.95",
            "reason": "Top rated ergonomic wireless mouse with silent clicks",
        }
    ])

    orchestrator = AgentOrchestrator(discovery_service=mock_discovery)
    await orchestrator.execute_request_pipeline(
        request_id=req.id,
        user_id=test_user.id,
        worker_id="test_worker_1",
        db=db,
    )

    db.refresh(req)
    assert req.status == RequestStatus.PROPOSAL_READY.value
    assert req.completed_at is not None

    # Proposal must be persisted in database
    proposal = db.query(Proposal).filter_by(request_id=req.id).first()
    assert proposal is not None
    assert proposal.status == "pending"
    assert proposal.subtotal_at_proposal == Decimal("45.00")
    assert proposal.currency == "USD"
    assert proposal.user_id == test_user.id

    # Verify event sequence
    events = req_svc.get_request_events(req.id)
    event_types = [e.event_type for e in events]
    assert "search_started" in event_types
    assert "search_results_received" in event_types
    assert "candidate_refreshed" in event_types
    assert "guardrail_passed" in event_types
    assert "verification_started" in event_types
    assert "verification_completed" in event_types
    assert "proposal_ready" in event_types
    assert event_types[-1] == "proposal_ready"


@pytest.mark.anyio
async def test_orchestration_pipeline_no_match(db, active_mandate, test_user):
    """Test 6: Pipeline with 0 discovery candidates transitions cleanly to no_match."""
    req_svc = RequestService(db)
    req = req_svc.create_request(
        user_id=test_user.id,
        request_in=type("Payload", (), {
            "text": "Antigravity levitation shoes size 10",
            "filters": None,
        })(),
    )

    # Empty candidate results
    mock_discovery = MockDiscoveryService([])
    orchestrator = AgentOrchestrator(discovery_service=mock_discovery)
    await orchestrator.execute_request_pipeline(
        request_id=req.id,
        user_id=test_user.id,
        worker_id="test_worker_2",
        db=db,
    )

    db.refresh(req)
    assert req.status == RequestStatus.NO_MATCH.value
    assert req.error_code == CartiErrorCode.NO_ELIGIBLE_PRODUCTS
    assert req.completed_at is not None

    # No proposal created
    assert db.query(Proposal).filter_by(request_id=req.id).count() == 0

    events = req_svc.get_request_events(req.id)
    event_types = [e.event_type for e in events]
    assert "no_match" in event_types
    assert event_types[-1] == "no_match"


@pytest.mark.anyio
async def test_orchestration_pipeline_guardrail_blocked(db, active_mandate, test_user):
    """Test 7: Pipeline where all candidates exceed budget cap transitions to blocked."""
    req_svc = RequestService(db)
    req = req_svc.create_request(
        user_id=test_user.id,
        request_in=type("Payload", (), {
            "text": "Luxury diamond desk lamp",
            "filters": None,
        })(),
    )

    # Product price $350.00 exceeds per_item_cap ($50.00)
    mock_discovery = MockDiscoveryService([
        {
            "product_id": "ch3_expensive_lamp",
            "title": "Diamond Encrusted Lamp",
            "price": "350.00",
            "domain": "luxury.com",
            "availability": "InStock",
            "condition": "new",
        }
    ])

    orchestrator = AgentOrchestrator(discovery_service=mock_discovery)
    await orchestrator.execute_request_pipeline(
        request_id=req.id,
        user_id=test_user.id,
        worker_id="test_worker_3",
        db=db,
    )

    db.refresh(req)
    assert req.status == RequestStatus.BLOCKED.value
    assert req.error_code == CartiErrorCode.GUARDRAIL_BLOCKED
    assert req.completed_at is not None

    # Verify blocked terminal event
    events = req_svc.get_request_events(req.id)
    event_types = [e.event_type for e in events]
    assert "guardrail_blocked" in event_types
    assert "request_blocked" in event_types
    assert event_types[-1] == "request_blocked"


@pytest.mark.anyio
async def test_cancellation_stops_worker_at_checkpoint(db, active_mandate, test_user):
    """Test 8: User cancellation stops execution and prevents proposal creation."""
    req_svc = RequestService(db)
    req = req_svc.create_request(
        user_id=test_user.id,
        request_in=type("Payload", (), {
            "text": "Cancel test request",
            "filters": None,
        })(),
    )

    # Cancel request before/during pipeline
    req_svc.cancel_request(req.id, test_user.id)
    db.refresh(req)
    assert req.status == RequestStatus.CANCELLED.value

    # Run orchestrator
    mock_discovery = MockDiscoveryService([
        {
            "product_id": "item_1",
            "title": "Some Product",
            "price": "20.00",
            "domain": "target.com",
            "availability": "InStock",
        }
    ])
    orchestrator = AgentOrchestrator(discovery_service=mock_discovery)
    await orchestrator.execute_request_pipeline(
        request_id=req.id,
        user_id=test_user.id,
        worker_id="test_worker_4",
        db=db,
    )

    # Request remains cancelled and NO proposal was generated
    db.refresh(req)
    assert req.status == RequestStatus.CANCELLED.value
    assert db.query(Proposal).filter_by(request_id=req.id).count() == 0


def test_cross_user_request_isolation_and_idor(client, valid_request, other_user):
    """Test 9: Cross-user IDOR access is strictly rejected with 403 ACCESS_DENIED."""
    other_headers = {"Authorization": f"Bearer {other_user.id}"}

    # 1. GET /api/requests/{id}
    res_get = client.get(f"/api/requests/{valid_request.id}", headers=other_headers)
    assert res_get.status_code == 403
    assert res_get.json()["error"]["code"] == CartiErrorCode.ACCESS_DENIED

    # 2. GET /api/requests/{id}/stream
    res_stream = client.get(f"/api/requests/{valid_request.id}/stream", headers=other_headers)
    assert res_stream.status_code == 403
    assert res_stream.json()["error"]["code"] == CartiErrorCode.ACCESS_DENIED

    # 3. POST /api/requests/{id}/cancel
    res_cancel = client.post(f"/api/requests/{valid_request.id}/cancel", headers=other_headers)
    assert res_cancel.status_code == 403
    assert res_cancel.json()["error"]["code"] == CartiErrorCode.ACCESS_DENIED

    # 4. GET /api/requests/{id}/candidates
    res_cand = client.get(f"/api/requests/{valid_request.id}/candidates", headers=other_headers)
    assert res_cand.status_code == 403
    assert res_cand.json()["error"]["code"] == CartiErrorCode.ACCESS_DENIED


def test_event_payload_sanitization_no_secret_leak(db, valid_request):
    """Test 10: Event payloads strip sensitive tokens and passwords before persistence."""
    req_svc = RequestService(db)
    ev = req_svc.add_request_event(
        request_id=valid_request.id,
        event_type="test_event",
        payload={
            "safe_step": "step_1",
            "access_token": "secret_bearer_token_xyz",
            "paypal_client_secret": "super_secret_key",
            "password": "my_password",
            "nested": {
                "ok_field": "fine",
                "secret": "leaked_secret",
            },
        },
    )
    db.refresh(ev)
    assert "access_token" not in ev.payload
    assert "paypal_client_secret" not in ev.payload
    assert "password" not in ev.payload
    assert ev.payload["safe_step"] == "step_1"
    assert "secret" not in ev.payload["nested"]
    assert ev.payload["nested"]["ok_field"] == "fine"


def test_terminal_event_breaks_stream(client, db, valid_request):
    """Test 11: SSE stream terminates after encountering a terminal event."""
    ev1 = RequestEvent(
        request_id=valid_request.id,
        event_type="search_started",
        payload={"step": "search_started"},
    )
    ev2 = RequestEvent(
        request_id=valid_request.id,
        event_type="no_match",
        payload={"step": "no_match", "message": "Zero results"},
    )
    # Extra event after terminal (should not be reached)
    ev3 = RequestEvent(
        request_id=valid_request.id,
        event_type="late_event",
        payload={"step": "late"},
    )
    db.add_all([ev1, ev2, ev3])
    db.commit()

    res = client.get(f"/api/requests/{valid_request.id}/stream")
    assert res.status_code == 200
    assert "event: search_started" in res.text
    assert "event: no_match" in res.text
    assert "event: late_event" not in res.text
