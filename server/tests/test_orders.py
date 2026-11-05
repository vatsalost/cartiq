"""Tests for payment capture, refunds, receipt, and order history."""

from decimal import Decimal
import uuid
from server.app.models.order import Order


def test_payment_capture_delegation(client, sample_proposal, db, test_user):
    """Test 16: Payment capture transitions order to completed with capture ID."""
    # First create order
    order_res = client.post(
        f"/api/proposals/{sample_proposal.id}/order",
        json={"checkout_attempt_id": "attempt_cap_1"},
    )
    order_id = order_res.json()["order_id"]

    # Now capture payment
    capture_res = client.post(
        f"/api/orders/{order_id}/capture",
        json={"paypal_order_id": order_res.json()["paypal_order_id"]},
    )
    assert capture_res.status_code == 200
    cap_data = capture_res.json()
    assert cap_data["status"] == "completed"
    assert "paypal_capture_id" in cap_data

    # Idempotency test: capturing again returns same completed status
    retry_res = client.post(f"/api/orders/{order_id}/capture")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "completed"


def test_refund_validation(client, sample_proposal, db):
    """Test 17: Refund on completed payment succeeds; uncaptured order fails."""
    # Create order directly in 'created' state (uncaptured)
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=sample_proposal.user_id,
        paypal_order_id="PP-ORD-TEST",
        create_request_id="req_test_1",
        amount=Decimal("34.99"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Attempt refund on uncaptured order -> must fail
    fail_res = client.post(f"/api/orders/{order.id}/refund", json={"reason": "Changed mind"})
    assert fail_res.status_code == 400
    assert fail_res.json()["error"]["code"] == "REFUND_NOT_ALLOWED"

    # Mark completed with capture ID
    order.status = "completed"
    order.paypal_capture_id = "CAP-TEST-123"
    db.commit()

    # Attempt refund now -> succeeds
    refund_res = client.post(f"/api/orders/{order.id}/refund", json={"reason": "Product damaged"})
    assert refund_res.status_code == 200
    ref_data = refund_res.json()
    assert ref_data["status"] == "completed"
    assert ref_data["amount"] == "34.99"


def test_order_history_and_receipt(client, sample_proposal, db):
    """Test 18: Order list pagination and full receipt retrieval."""
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=sample_proposal.user_id,
        paypal_order_id="PP-ORD-RECEIPT",
        paypal_capture_id="CAP-RECEIPT",
        create_request_id="req_receipt_1",
        amount=Decimal("34.99"),
        currency="USD",
        status="completed",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    db.commit()

    # List orders
    list_res = client.get("/api/orders?limit=10&offset=0")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert len(list_data["items"]) >= 1

    # Get receipt
    receipt_res = client.get(f"/api/orders/{order.id}")
    assert receipt_res.status_code == 200
    receipt_data = receipt_res.json()
    assert receipt_data["id"] == str(order.id)
    assert receipt_data["product_title"] == "Modern Adjustable Desk Lamp"
    assert "Sandbox payment completed" in receipt_data["fulfillment_note"]
