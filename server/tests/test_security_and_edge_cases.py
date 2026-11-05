"""Comprehensive security, IDOR, input validation, and edge-case test suite."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from server.app.core.config import settings
from server.app.models.order import Order
from server.app.models.proposal import Proposal


def test_malformed_uuid_parameters(client):
    """Malformed UUIDs in route paths are rejected with structured 422 errors."""
    get_paths = [
        "/api/requests/not-a-real-uuid",
        "/api/requests/not-a-real-uuid/stream",
        "/api/requests/not-a-real-uuid/candidates",
        "/api/proposals/not-a-real-uuid",
        "/api/orders/not-a-real-uuid",
    ]
    post_paths = [
        "/api/requests/not-a-real-uuid/cancel",
        "/api/proposals/not-a-real-uuid/order",
        "/api/orders/not-a-real-uuid/capture",
        "/api/orders/not-a-real-uuid/refund",
    ]
    for path in get_paths:
        res = client.get(path)
        assert res.status_code == 422, f"Expected 422 for malformed UUID on GET {path}, got {res.status_code}"
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"

    for path in post_paths:
        res = client.post(path)
        assert res.status_code == 422, f"Expected 422 for malformed UUID on POST {path}, got {res.status_code}"
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_request_text_whitespace_and_length_boundaries(client, active_mandate):
    """Whitespace-only or overly long request text is rejected."""
    # 1. Whitespace only
    res1 = client.post("/api/requests", json={"text": "     "})
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Under minimum length
    res2 = client.post("/api/requests", json={"text": "ab"})
    assert res2.status_code == 422

    # 3. Over maximum length (1001 characters)
    long_text = "a" * 1001
    res3 = client.post("/api/requests", json={"text": long_text})
    assert res3.status_code == 422


def test_mandate_retailer_domain_syntax_validation(client):
    """Malformed retailer domains are rejected."""
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    for bad_domain in ["not a domain", "http://", "invalid..com", "domain!#$.com"]:
        res = client.post(
            "/api/mandates",
            json={
                "total_budget": "100.00",
                "per_item_cap": "50.00",
                "currency": "USD",
                "allowed_categories": ["Home"],
                "allowed_retailers": [bad_domain],
                "expires_at": future,
            },
        )
        assert res.status_code == 422, f"Expected 422 for retailer '{bad_domain}', got {res.status_code}"


def test_mandate_quantity_and_currency_edge_cases(client):
    """Quantity <= 0, > 50, and invalid currency codes fail validation."""
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()

    # Zero quantity
    res1 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "max_quantity_per_product": 0,
            "expires_at": future,
        },
    )
    assert res1.status_code == 422

    # Invalid currency
    for bad_curr in ["US", "USDD", "123", "$$$"]:
        res = client.post(
            "/api/mandates",
            json={
                "total_budget": "100.00",
                "per_item_cap": "50.00",
                "currency": bad_curr,
                "allowed_categories": ["Home"],
                "expires_at": future,
            },
        )
        assert res.status_code == 422


def test_cannot_reduce_mandate_below_active_spend(client, active_mandate, sample_proposal, db):
    """A user cannot reduce their mandate budget below already committed/reserved spend."""
    # Create an order reserving $34.99
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=active_mandate.user_id,
        paypal_order_id="PP-ORD-LOCK",
        create_request_id="req_lock_1",
        amount=Decimal("34.99"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    db.commit()

    # Attempt to create new mandate version with budget $20.00 (< $34.99 committed)
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "20.00",
            "per_item_cap": "20.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future,
        },
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BUDGET_EXCEEDED"


def test_idor_cross_user_mandate_access(client, active_mandate, other_user):
    """Users cannot view or affect other users' mandates."""
    # When other_user asks for /api/mandates/current, they shouldn't see test_user's mandate
    headers = {"Authorization": f"Bearer {other_user.id}"}
    res = client.get("/api/mandates/current", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "MANDATE_NOT_FOUND"


def test_idor_cross_user_order_access(client, sample_proposal, other_user, db):
    """Users cannot view or capture another user's order."""
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=sample_proposal.user_id,
        paypal_order_id="PP-ORD-IDOR",
        create_request_id="req_idor_1",
        amount=Decimal("34.99"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    db.commit()

    headers = {"Authorization": f"Bearer {other_user.id}"}

    # Attempt to read receipt
    res1 = client.get(f"/api/orders/{order.id}", headers=headers)
    assert res1.status_code == 403
    assert res1.json()["error"]["code"] == "ACCESS_DENIED"

    # Attempt to capture
    res2 = client.post(f"/api/orders/{order.id}/capture", headers=headers)
    assert res2.status_code == 403

    # Attempt to refund
    res3 = client.post(f"/api/orders/{order.id}/refund", headers=headers)
    assert res3.status_code == 403


def test_order_capture_paypal_order_id_mismatch(client, sample_proposal, db):
    """Mismatched PayPal order ID in capture body is rejected."""
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=sample_proposal.user_id,
        paypal_order_id="PP-LEGIT-123",
        create_request_id="req_mismatch_1",
        amount=Decimal("34.99"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    db.commit()

    res = client.post(
        f"/api/orders/{order.id}/capture",
        json={"paypal_order_id": "PP-FORGED-999"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "PAYMENT_CAPTURE_FAILED"
    assert "mismatch" in res.json()["error"]["message"].lower()


def test_duplicate_checkout_attempt_idempotency(client, sample_proposal):
    """Retrying order creation with identical attempt ID returns existing order idempotently."""
    attempt_id = "attempt_unique_999"

    # 1. First checkout call
    res1 = client.post(
        f"/api/proposals/{sample_proposal.id}/order",
        json={"checkout_attempt_id": attempt_id},
    )
    assert res1.status_code == 201
    order1 = res1.json()

    # 2. Retry with same checkout_attempt_id
    res2 = client.post(
        f"/api/proposals/{sample_proposal.id}/order",
        json={"checkout_attempt_id": attempt_id},
    )
    assert res2.status_code == 201
    order2 = res2.json()
    assert order1["order_id"] == order2["order_id"]
    assert order1["paypal_order_id"] == order2["paypal_order_id"]


def test_duplicate_cancellation_idempotency(client, valid_request):
    """Cancelling a request multiple times returns cancelled status without error."""
    res1 = client.post(f"/api/requests/{valid_request.id}/cancel")
    assert res1.status_code == 200
    assert res1.json()["status"] == "cancelled"

    res2 = client.post(f"/api/requests/{valid_request.id}/cancel")
    assert res2.status_code == 200
    assert res2.json()["status"] == "cancelled"


def test_invalid_bearer_token_rejection(client):
    """Invalid token format fails with 401 AUTHENTICATION_REQUIRED."""
    headers = {"Authorization": "Bearer not-a-uuid-and-not-demo"}
    res = client.get("/api/mandates/current", headers=headers)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_webhook_malformed_json_and_missing_event_id(client):
    """Malformed webhook body or missing event ID returns 400 error."""
    # 1. Invalid JSON body
    headers = {
        "PAYPAL-AUTH-ALGO": "SHA256withRSA",
        "PAYPAL-TRANSMISSION-ID": "trans_1",
        "PAYPAL-TRANSMISSION-SIG": "VALID_SIGNATURE",
        "PAYPAL-TRANSMISSION-TIME": "2026-11-03T12:00:00Z",
        "Content-Type": "application/json",
    }
    res1 = client.post("/api/webhooks/paypal", content="not json {", headers=headers)
    assert res1.status_code == 400
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Valid JSON but missing 'id'
    res2 = client.post("/api/webhooks/paypal", json={"event_type": "PAYMENT.CAPTURE.COMPLETED"}, headers=headers)
    assert res2.status_code == 400
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "Missing event ID" in res2.json()["error"]["message"]


def test_nonexistent_resources_return_404(client):
    """Querying non-existent UUIDs returns clean 404 errors."""
    random_id = uuid.uuid4()
    for path in [
        f"/api/requests/{random_id}",
        f"/api/requests/{random_id}/candidates",
        f"/api/proposals/{random_id}",
        f"/api/orders/{random_id}",
    ]:
        res = client.get(path)
        assert res.status_code == 404
        assert "NOT_FOUND" in res.json()["error"]["code"]
