"""Comprehensive tests for Backend Module B2: User Ownership Boundaries & Cross-Resource Isolation."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest
from server.app.models.user import User


@pytest.fixture
def user_a(db):
    """Create User A in db."""
    user = User(
        id=uuid.uuid4(),
        email="user_a@carti.local",
        is_active=True,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_b(db):
    """Create User B in db."""
    user = User(
        id=uuid.uuid4(),
        email="user_b@carti.local",
        is_active=True,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_a_mandate(db, user_a):
    """Active mandate for User A."""
    mandate = Mandate(
        user_id=user_a.id,
        version=1,
        total_budget=Decimal("200.00"),
        per_item_cap=Decimal("100.00"),
        currency="USD",
        allowed_categories=["Electronics", "Home"],
        blocked_categories=["Clothing"],
        allowed_retailers=["bestbuy.com", "target.com"],
        max_quantity_per_product=2,
        price_tolerance_pct=Decimal("0.0500"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        status="active",
    )
    db.add(mandate)
    db.commit()
    db.refresh(mandate)
    return mandate


@pytest.fixture
def user_a_request(db, user_a, user_a_mandate):
    """Shopping request for User A."""
    req = ShoppingRequest(
        user_id=user_a.id,
        mandate_id=user_a_mandate.id,
        request_text="Find wireless noise cancelling headphones under $80",
        normalized_intent={"category": "Electronics", "max_price": "80.00"},
        status="running",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def user_a_proposal(db, user_a, user_a_mandate, user_a_request):
    """Purchase proposal for User A."""
    candidate = Candidate(
        request_id=user_a_request.id,
        provider_product_id="TEST-PROD-B2-01",
        title="Anker Soundcore Space Q45",
        category="Electronics",
        rank_score=Decimal("0.95"),
    )
    db.add(candidate)
    db.flush()

    offer = CandidateOffer(
        candidate_id=candidate.id,
        domain="bestbuy.com",
        buy_url="https://bestbuy.com/products/anker-q45",
        price_amount=Decimal("79.99"),
        currency="USD",
        availability="InStock",
    )
    db.add(offer)
    db.flush()

    proposal = Proposal(
        request_id=user_a_request.id,
        mandate_id=user_a_mandate.id,
        candidate_id=candidate.id,
        offer_id=offer.id,
        user_id=user_a.id,
        unit_price_at_proposal=Decimal("79.99"),
        subtotal_at_proposal=Decimal("79.99"),
        currency="USD",
        quantity=1,
        rationale="Top pick for noise-cancelling headphones.",
        guardrail_result={"passed": True, "checks": []},
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@pytest.fixture
def user_a_order(db, user_a, user_a_proposal):
    """Captured order for User A."""
    order = Order(
        proposal_id=user_a_proposal.id,
        user_id=user_a.id,
        paypal_order_id="TEST-PP-ORD-A1",
        paypal_capture_id="TEST-PP-CAP-A1",
        create_request_id="req-user-a-order",
        amount=Decimal("79.99"),
        currency="USD",
        status="completed",
        budget_reserved=Decimal("79.99"),
        captured_at=datetime.now(timezone.utc),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def test_mandate_isolation(client, user_a, user_b, user_a_mandate):
    """User B should not see User A's mandate."""
    # User A gets current mandate
    res_a = client.get("/api/mandates/current", headers={"Authorization": f"Bearer {user_a.id}"})
    assert res_a.status_code == 200
    assert res_a.json()["id"] == str(user_a_mandate.id)

    # User B gets current mandate (none found for User B)
    res_b = client.get("/api/mandates/current", headers={"Authorization": f"Bearer {user_b.id}"})
    assert res_b.status_code == 404
    assert res_b.json()["error"]["code"] == "MANDATE_NOT_FOUND"


def test_shopping_request_isolation(client, user_a, user_b, user_a_request):
    """User B cannot view or cancel User A's shopping request."""
    # User B status lookup
    res_status = client.get(
        f"/api/requests/{user_a_request.id}",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_status.status_code == 403
    assert res_status.json()["error"]["code"] == "ACCESS_DENIED"

    # User B cancellation
    res_cancel = client.post(
        f"/api/requests/{user_a_request.id}/cancel",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_cancel.status_code == 403
    assert res_cancel.json()["error"]["code"] == "ACCESS_DENIED"

    # User B candidate access
    res_cand = client.get(
        f"/api/requests/{user_a_request.id}/candidates",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_cand.status_code == 403
    assert res_cand.json()["error"]["code"] == "ACCESS_DENIED"


def test_proposal_isolation(client, user_a, user_b, user_a_proposal):
    """User B cannot view User A's proposal or create order from it."""
    # View proposal
    res_view = client.get(
        f"/api/proposals/{user_a_proposal.id}",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_view.status_code == 403
    assert res_view.json()["error"]["code"] == "ACCESS_DENIED"

    # Create order from User A's proposal
    res_order = client.post(
        f"/api/proposals/{user_a_proposal.id}/order",
        json={"checkout_attempt_id": "attempt-hack-123"},
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_order.status_code == 403
    assert res_order.json()["error"]["code"] == "ACCESS_DENIED"


def test_order_and_refund_isolation(client, user_a, user_b, user_a_order):
    """User B cannot view receipt, capture, or refund User A's order."""
    # View receipt
    res_view = client.get(
        f"/api/orders/{user_a_order.id}",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_view.status_code == 403
    assert res_view.json()["error"]["code"] == "ACCESS_DENIED"

    # Attempt capture
    res_cap = client.post(
        f"/api/orders/{user_a_order.id}/capture",
        json={"paypal_order_id": "FAKE"},
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_cap.status_code == 403
    assert res_cap.json()["error"]["code"] == "ACCESS_DENIED"

    # Attempt refund
    res_ref = client.post(
        f"/api/orders/{user_a_order.id}/refund",
        json={"reason": "Unauthorized refund attempt"},
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res_ref.status_code == 403
    assert res_ref.json()["error"]["code"] == "ACCESS_DENIED"


def test_order_history_isolation(client, user_a, user_b, user_a_order):
    """User B's order history does not leak User A's orders."""
    res_a = client.get("/api/orders", headers={"Authorization": f"Bearer {user_a.id}"})
    assert res_a.status_code == 200
    assert res_a.json()["total"] >= 1
    order_ids_a = [o["id"] for o in res_a.json()["items"]]
    assert str(user_a_order.id) in order_ids_a

    res_b = client.get("/api/orders", headers={"Authorization": f"Bearer {user_b.id}"})
    assert res_b.status_code == 200
    assert res_b.json()["total"] == 0
    assert len(res_b.json()["items"]) == 0


def test_cross_resource_tampering_detection(client, db, user_a, user_b, user_a_mandate, user_a_request):
    """
    Test defense against manipulated associations:
    If a proposal's user_id is changed to User B, but its associated request/mandate
    belong to User A, accessing the proposal must fail with ACCESS_DENIED.
    """
    candidate = Candidate(
        request_id=user_a_request.id,
        provider_product_id="TEST-PROD-B2-02",
        title="Tampered Product",
        category="Electronics",
        rank_score=Decimal("0.80"),
    )
    db.add(candidate)
    db.flush()

    offer = CandidateOffer(
        candidate_id=candidate.id,
        domain="bestbuy.com",
        buy_url="https://bestbuy.com/products/tampered",
        price_amount=Decimal("50.00"),
        currency="USD",
        availability="InStock",
    )
    db.add(offer)
    db.flush()

    # Tampered proposal: owned by user_b, but referencing user_a's request & mandate
    tampered_proposal = Proposal(
        request_id=user_a_request.id,
        mandate_id=user_a_mandate.id,
        candidate_id=candidate.id,
        offer_id=offer.id,
        user_id=user_b.id,
        unit_price_at_proposal=Decimal("50.00"),
        subtotal_at_proposal=Decimal("50.00"),
        currency="USD",
        quantity=1,
        rationale="Tampered proposal for isolation test.",
        guardrail_result={"passed": True, "checks": []},
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(tampered_proposal)
    db.commit()
    db.refresh(tampered_proposal)

    # User B tries to view this tampered proposal
    res = client.get(
        f"/api/proposals/{tampered_proposal.id}",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"
    assert "associated" in res.json()["error"]["message"].lower()


def test_user_id_spoofing_ignored_in_request_body(client, user_a, user_b, user_a_mandate):
    """
    Verify client cannot specify user_id in the request payload to act on behalf of another user.
    """
    spoofed_payload = {
        "text": "Find a modern LED desk lamp",
        "user_id": str(user_b.id),
        "mandate_id": str(uuid.uuid4()),
        "filters": {"category": "Home", "max_price": "50.00"},
    }
    # User A submits the request
    res = client.post(
        "/api/requests",
        json=spoofed_payload,
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 202
    req_id = res.json()["request_id"]

    # Verify that the created request is owned by user_a, not user_b
    req_status = client.get(
        f"/api/requests/{req_id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert req_status.status_code == 200

    # User B cannot access it
    req_status_b = client.get(
        f"/api/requests/{req_id}",
        headers={"Authorization": f"Bearer {user_b.id}"},
    )
    assert req_status_b.status_code == 403
