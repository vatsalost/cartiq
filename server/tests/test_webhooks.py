"""Tests for PayPal webhook verification and event deduplication."""

from decimal import Decimal
from server.app.models.order import Order


def test_invalid_webhook_signature(client):
    """Test 19: Missing or invalid signature returns 400 error."""
    payload = {
        "id": "WH-EVT-1",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {"id": "CAP-123"},
    }
    # Headers with bad signature
    headers = {
        "PAYPAL-AUTH-ALGO": "SHA256withRSA",
        "PAYPAL-TRANSMISSION-ID": "trans_1",
        "PAYPAL-TRANSMISSION-SIG": "INVALID_SIGNATURE",
        "PAYPAL-TRANSMISSION-TIME": "2026-11-03T12:00:00Z",
    }
    res = client.post("/api/webhooks/paypal", json=payload, headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "WEBHOOK_SIGNATURE_INVALID"


def test_duplicate_webhook_event(client, sample_proposal, db):
    """Test 20: Duplicate webhook events are handled idempotently without error."""
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=sample_proposal.user_id,
        paypal_order_id="PP-ORD-WH",
        create_request_id="req_wh_1",
        amount=Decimal("34.99"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    db.commit()

    payload = {
        "id": "WH-UNIQUE-EVT-999",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {"id": "PP-ORD-WH"},
    }
    headers = {
        "PAYPAL-AUTH-ALGO": "SHA256withRSA",
        "PAYPAL-TRANSMISSION-ID": "trans_unique",
        "PAYPAL-TRANSMISSION-SIG": "VALID_SIGNATURE_TEST",
        "PAYPAL-TRANSMISSION-TIME": "2026-11-03T12:00:00Z",
    }

    # 1. First delivery
    res1 = client.post("/api/webhooks/paypal", json=payload, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"

    # Order should be reconciled to completed
    db.refresh(order)
    assert order.status == "completed"

    # 2. Duplicate delivery (PayPal retry)
    res2 = client.post("/api/webhooks/paypal", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "success"
