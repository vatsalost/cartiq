"""Module B10: PayPal Payment Service and Payment Lifecycle comprehensive test suite.

Verifies:
A. PayPal client tests (OAuth token caching, creation, capture, refund, timeout, rate limit)
B. Checkout validation through B9 (prep contract, expired/stale proposals, budget checks)
C. Order creation & idempotency (stable keys, duplicate prevention, backend amount authority)
D. Server-side payment capture (buyer approval, duplicate callbacks, state validation)
E. Refund execution (full & partial refunds, cap limits, uncaptured rejection, idempotency)
F. State machine & concurrency (transitions, cancellation, reconciliation, terminal protection)
G. Multi-tenant security & IDOR protection (cross-user access, credential isolation)
H. B11 Webhook & B3 budget reservation reconciliation
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import httpx
import pytest
from sqlalchemy import select

from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.refund import Refund
from server.app.models.user import User
from server.app.services.mandate_service import MandateService
from server.app.services.order_service import OrderService
from server.app.services.paypal_service import PayPalService, paypal_service
from server.app.services.proposal_service import ProposalService
from server.app.services.webhook_service import WebhookService


@pytest.fixture
def order_service(db):
    return OrderService(db)


@pytest.fixture
def test_order(db, sample_proposal, test_user):
    """Create a sample order in 'created' status."""
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        paypal_order_id="PP-SANDBOX-ORDER-1234",
        create_request_id="req_test_order_1234",
        amount=sample_proposal.total_amount,
        currency=sample_proposal.currency,
        status="created",
        budget_reserved=sample_proposal.total_amount,
    )
    db.add(order)
    sample_proposal.status = "checkout_started"
    db.commit()
    db.refresh(order)
    return order


# =====================================================================
# SECTION A: PAYPAL CLIENT TESTS
# =====================================================================

def test_paypal_client_token_caching():
    """Test A1: OAuth token acquisition caches token safely and reuses before expiration."""
    client = PayPalService()
    t1 = client.get_access_token()
    assert t1 is not None
    assert client._cached_token == t1
    assert client._token_expires_at is not None

    # Immediate second call returns cached token without re-requesting
    t2 = client.get_access_token()
    assert t2 == t1


def test_paypal_client_create_order_result_properties(sample_proposal):
    """Test A2: Order creation returns tuple with paypal_order_id, amount, currency, and approval_url."""
    res = paypal_service.create_order(sample_proposal, "test_attempt_1")
    # Unpacks as 3 elements for backwards compatibility
    oid, amt, curr = res
    assert oid.startswith("PP-SANDBOX-")
    assert amt == sample_proposal.total_amount
    assert curr == "USD"
    # Also exposes approval_url attribute
    assert res.approval_url is not None
    assert "sandbox.paypal.com" in res.approval_url
    assert oid in res.approval_url


def test_paypal_client_get_order():
    """Test A3: Inspect PayPal order by ID returns validated payload."""
    details = paypal_service.get_order("PP-SANDBOX-ORDER-123")
    assert details["id"] == "PP-SANDBOX-ORDER-123"
    assert "status" in details


def test_paypal_client_capture():
    """Test A4: Capture PayPal order returns deterministic capture ID and completed timestamp."""
    cap_id, amt, curr, captured_at = paypal_service.capture_order(
        "PP-SANDBOX-ORDER-123", "idemp_cap_key_1"
    )
    assert cap_id.startswith("CAP-")
    assert captured_at is not None


def test_paypal_client_refund():
    """Test A5: Refund completed capture returns refund ID and completed status."""
    ref_id, status = paypal_service.refund_capture(
        "CAP-12345678", Decimal("34.99"), "USD", "idemp_ref_key_1"
    )
    assert ref_id.startswith("REF-")
    assert status == "completed"


def test_paypal_client_timeout_handling(monkeypatch):
    """Test A6: HTTP timeout translates to structured 504 DOWNSTREAM_SERVICE_UNAVAILABLE."""
    svc = PayPalService()
    svc.client_id = "real_mock_client_id"
    svc.client_secret = "real_mock_client_secret"

    def mock_post(*args, **kwargs):
        raise httpx.TimeoutException("Connection timed out")

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    with pytest.raises(CartiAPIException) as exc:
        svc.get_access_token()
    assert exc.value.code == CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE
    assert exc.value.status_code == 504
    assert exc.value.retryable is True


# =====================================================================
# SECTION B: CHECKOUT VALIDATION THROUGH B9
# =====================================================================

def test_order_creation_enforces_b9_checkout_prep(order_service, sample_proposal, test_user):
    """Test B1: Order creation uses B9 checkout preparation and uses server-calculated amount."""
    order = order_service.create_order_from_proposal(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        checkout_attempt_id="attempt_b9_prep_1",
    )
    assert order.id is not None
    assert order.amount == sample_proposal.total_amount
    assert order.currency == sample_proposal.currency
    assert order.status == "created"
    assert order.budget_reserved == sample_proposal.total_amount


def test_order_creation_rejects_expired_proposal(order_service, db, sample_proposal, test_user):
    """Test B2: Order creation rejects proposal that has expired."""
    sample_proposal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        order_service.create_order_from_proposal(
            proposal_id=sample_proposal.id,
            user_id=test_user.id,
            checkout_attempt_id="attempt_expired",
        )
    assert exc.value.code == CartiErrorCode.PROPOSAL_EXPIRED


def test_order_creation_rejects_stale_offer_stock(order_service, db, sample_proposal, test_user):
    """Test B3: Order creation rejects proposal when retailer offer goes out of stock."""
    sample_proposal.offer.availability = "OutOfStock"
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        order_service.create_order_from_proposal(
            proposal_id=sample_proposal.id,
            user_id=test_user.id,
            checkout_attempt_id="attempt_out_of_stock",
        )
    assert exc.value.code == CartiErrorCode.PROPOSAL_STALE


def test_order_creation_rejects_insufficient_budget(order_service, db, sample_proposal, test_user, active_mandate):
    """Test B4: Order creation rejects when order amount exceeds remaining mandate budget."""
    active_mandate.total_budget = Decimal("20.00")  # Proposal is 34.99 > 20.00
    active_mandate.per_item_cap = Decimal("20.00")
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        order_service.create_order_from_proposal(
            proposal_id=sample_proposal.id,
            user_id=test_user.id,
            checkout_attempt_id="attempt_budget_exceeded",
        )
    assert exc.value.code == CartiErrorCode.BUDGET_EXCEEDED


# =====================================================================
# SECTION C: ORDER CREATION & IDEMPOTENCY
# =====================================================================

def test_order_creation_idempotency(order_service, sample_proposal, test_user):
    """Test C1: Repeated order creation with same attempt ID returns existing order."""
    o1 = order_service.create_order_from_proposal(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        checkout_attempt_id="stable_attempt_123",
    )
    o2 = order_service.create_order_from_proposal(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        checkout_attempt_id="stable_attempt_123",
    )
    assert o1.id == o2.id
    assert o1.paypal_order_id == o2.paypal_order_id


def test_order_creation_prevents_duplicate_orders_for_different_attempts(order_service, sample_proposal, test_user):
    """Test C2: Cannot create a second distinct order for the same proposal."""
    order_service.create_order_from_proposal(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        checkout_attempt_id="attempt_first",
    )
    with pytest.raises(CartiAPIException) as exc:
        order_service.create_order_from_proposal(
            proposal_id=sample_proposal.id,
            user_id=test_user.id,
            checkout_attempt_id="attempt_different_second",
        )
    assert exc.value.code in [CartiErrorCode.PROPOSAL_STALE, CartiErrorCode.VALIDATION_ERROR]


# =====================================================================
# SECTION D: SERVER-SIDE PAYMENT CAPTURE
# =====================================================================

def test_payment_capture_success(order_service, test_order, test_user, active_mandate, db):
    """Test D1: Capturing order sets status to completed, records capture ID, and converts reservation."""
    captured = order_service.capture_order(
        order_id=test_order.id,
        user_id=test_user.id,
        paypal_order_id=test_order.paypal_order_id,
    )
    assert captured.status == "completed"
    assert captured.paypal_capture_id is not None
    assert captured.captured_at is not None

    # Proposal state is updated to ordered
    db.refresh(test_order.proposal)
    assert test_order.proposal.status == "ordered"

    # In B3, reservation is converted to confirmed captured spend
    breakdown = order_service.mandate_service.calculate_available_budget(active_mandate.id)
    assert breakdown.captured_spending == test_order.amount
    assert breakdown.active_reservations == Decimal("0.00")


def test_payment_capture_idempotent(order_service, test_order, test_user):
    """Test D2: Repeated capture request on completed order is idempotent."""
    c1 = order_service.capture_order(test_order.id, test_user.id)
    assert c1.status == "completed"

    c2 = order_service.capture_order(test_order.id, test_user.id)
    assert c2.status == "completed"
    assert c2.paypal_capture_id == c1.paypal_capture_id


def test_payment_capture_rejects_unrelated_order_id(order_service, test_order, test_user):
    """Test D3: Rejects capture if client supplies mismatched paypal_order_id."""
    with pytest.raises(CartiAPIException) as exc:
        order_service.capture_order(
            order_id=test_order.id,
            user_id=test_user.id,
            paypal_order_id="PP-MISMATCHED-ID",
        )
    assert exc.value.code == CartiErrorCode.PAYMENT_CAPTURE_FAILED


# =====================================================================
# SECTION E: REFUND EXECUTION (FULL & PARTIAL)
# =====================================================================

def test_full_refund_execution(order_service, test_order, test_user, db):
    """Test E1: Full refund for a completed order updates status to refunded and clears reservations."""
    order_service.capture_order(test_order.id, test_user.id)

    refund = order_service.refund_order(test_order.id, test_user.id, reason="Customer return")
    assert refund.status == "completed"
    assert refund.amount == test_order.amount
    assert refund.paypal_refund_id is not None

    db.refresh(test_order)
    assert test_order.status == "refunded"
    assert test_order.budget_reserved == Decimal("0.00")


def test_partial_refund_execution(order_service, test_order, test_user, db):
    """Test E2: Partial refund records exact partial amount without marking order fully refunded."""
    order_service.capture_order(test_order.id, test_user.id)

    # First partial refund: $10.00
    ref1 = order_service.refund_order(test_order.id, test_user.id, reason="Partial adjustment", amount=Decimal("10.00"))
    assert ref1.amount == Decimal("10.00")
    db.refresh(test_order)
    assert test_order.status == "completed"  # Still partially captured

    # Attempt excessive refund > remaining ($34.99 - $10.00 = $24.99; requesting $25.00 -> rejected)
    with pytest.raises(CartiAPIException) as exc:
        order_service.refund_order(test_order.id, test_user.id, amount=Decimal("25.00"))
    assert exc.value.code == CartiErrorCode.REFUND_NOT_ALLOWED

    # Second partial refund for remaining $24.99 -> finishes full refund
    ref2 = order_service.refund_order(test_order.id, test_user.id, amount=Decimal("24.99"))
    assert ref2.amount == Decimal("24.99")
    db.refresh(test_order)
    assert test_order.status == "refunded"


def test_refund_rejects_uncaptured_order(order_service, test_order, test_user):
    """Test E3: Attempting to refund an order in 'created' state is rejected."""
    with pytest.raises(CartiAPIException) as exc:
        order_service.refund_order(test_order.id, test_user.id)
    assert exc.value.code == CartiErrorCode.REFUND_NOT_ALLOWED


# =====================================================================
# SECTION F: STATE MACHINE, CANCELLATION, & RECONCILIATION
# =====================================================================

def test_order_cancellation_releases_budget(order_service, test_order, test_user, active_mandate, db):
    """Test F1: Cancelling an uncaptured order releases budget reservation and resets proposal."""
    breakdown_before = order_service.mandate_service.calculate_available_budget(active_mandate.id)
    assert breakdown_before.active_reservations == test_order.amount

    cancelled = order_service.cancel_order(test_order.id, test_user.id, reason="Buyer aborted")
    assert cancelled.status == "cancelled"

    breakdown_after = order_service.mandate_service.calculate_available_budget(active_mandate.id)
    assert breakdown_after.active_reservations == Decimal("0.00")
    assert breakdown_after.available_budget == active_mandate.total_budget

    db.refresh(test_order.proposal)
    assert test_order.proposal.status == "pending"


def test_order_reconciliation_with_paypal(order_service, test_order, test_user, db):
    """Test F2: Reconciling order synchronizes status with live PayPal Orders v2 API."""
    reconciled = order_service.reconcile_order_with_paypal(test_order.id, test_user.id)
    assert reconciled.status in ["created", "buyer_approved", "completed"]


# =====================================================================
# SECTION G: MULTI-TENANT SECURITY & IDOR PROTECTION
# =====================================================================

def test_cross_user_order_access_forbidden(order_service, test_order, other_user):
    """Test G1: User B cannot capture, refund, or view receipt for User A's order."""
    # Capture attempt
    with pytest.raises(CartiAPIException) as exc1:
        order_service.capture_order(test_order.id, other_user.id)
    assert exc1.value.code == CartiErrorCode.ACCESS_DENIED

    # Refund attempt
    with pytest.raises(CartiAPIException) as exc2:
        order_service.refund_order(test_order.id, other_user.id)
    assert exc2.value.code == CartiErrorCode.ACCESS_DENIED

    # Receipt attempt
    with pytest.raises(CartiAPIException) as exc3:
        order_service.get_order_receipt(test_order.id, other_user.id)
    assert exc3.value.code == CartiErrorCode.ACCESS_DENIED

    # Cancel attempt
    with pytest.raises(CartiAPIException) as exc4:
        order_service.cancel_order(test_order.id, other_user.id)
    assert exc4.value.code == CartiErrorCode.ACCESS_DENIED


def test_api_orders_cross_user_rejection(client, test_order, other_user):
    """Test G2: REST API endpoints reject cross-user order capture and refund attempts."""
    headers = {"Authorization": f"Bearer {other_user.id}"}

    res_cap = client.post(f"/api/orders/{test_order.id}/capture", headers=headers)
    assert res_cap.status_code == 403
    assert res_cap.json()["error"]["code"] == "ACCESS_DENIED"

    res_ref = client.post(f"/api/orders/{test_order.id}/refund", headers=headers)
    assert res_ref.status_code == 403
    assert res_ref.json()["error"]["code"] == "ACCESS_DENIED"

    res_rec = client.get(f"/api/orders/{test_order.id}", headers=headers)
    assert res_rec.status_code == 403
    assert res_rec.json()["error"]["code"] == "ACCESS_DENIED"


# =====================================================================
# SECTION H: B11 WEBHOOK & B3 RESERVATION RECONCILIATION
# =====================================================================

def test_webhook_payment_capture_completed(db, test_order, active_mandate):
    """Test H1: Asynchronous capture webhook marks order completed and converts B3 reservation."""
    webhook_svc = WebhookService(db)
    payload = {
        "id": "WH-CAPTURE-COMPLETED-1",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {"id": test_order.paypal_order_id},
    }
    headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/cert.pem",
        "paypal-transmission-id": "trans-123",
        "paypal-transmission-sig": "valid-sig",
        "paypal-transmission-time": datetime.now(timezone.utc).isoformat(),
    }

    ok, event_id = webhook_svc.process_webhook(headers, b"{}", payload)
    assert ok is True
    assert event_id == "WH-CAPTURE-COMPLETED-1"

    db.refresh(test_order)
    assert test_order.status == "completed"

    breakdown = MandateService(db).calculate_available_budget(active_mandate.id)
    assert breakdown.captured_spending == test_order.amount
    assert breakdown.active_reservations == Decimal("0.00")


def test_webhook_older_capture_cannot_reverse_refund(db, test_order):
    """Test H2: Monotonic state check: older capture webhook cannot overwrite refunded order back to completed."""
    test_order.status = "refunded"
    test_order.budget_reserved = Decimal("0.00")
    db.commit()

    webhook_svc = WebhookService(db)
    payload = {
        "id": "WH-LATE-CAPTURE-1",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {"id": test_order.paypal_order_id},
    }
    headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/cert.pem",
        "paypal-transmission-id": "trans-456",
        "paypal-transmission-sig": "valid-sig",
        "paypal-transmission-time": datetime.now(timezone.utc).isoformat(),
    }

    webhook_svc.process_webhook(headers, b"{}", payload)

    db.refresh(test_order)
    assert test_order.status == "refunded"  # Remains refunded!


# =====================================================================
# SECTION I: MANDATORY RELEASE TESTS (TEST 1 - TEST 10)
# =====================================================================

def test_release_test_1_trusted_amount(client, db, test_user, active_mandate, sample_proposal):
    """
    MANDATORY TEST 1 — Trusted amount:
    Create a proposal with a trusted B9 checkout amount of $49.99.
    Submit a frontend checkout request attempting to change it to $1.00.
    Verify that PayPal receives $49.99, not $1.00.
    """
    # 1. Configure proposal with exact trusted amount of $49.99
    sample_proposal.offer.price_amount = Decimal("49.99")
    sample_proposal.unit_price_at_proposal = Decimal("49.99")
    sample_proposal.subtotal_at_proposal = Decimal("49.99")
    sample_proposal.shipping_amount = Decimal("0.00")
    sample_proposal.tax_amount = Decimal("0.00")
    sample_proposal.total_amount = Decimal("49.99")
    active_mandate.per_item_cap = Decimal("50.00")
    active_mandate.total_budget = Decimal("100.00")
    db.commit()

    # 2. Frontend attempt to tamper amount to $1.00
    headers = {"Authorization": f"Bearer {test_user.id}"}
    tampered_payload = {
        "checkout_attempt_id": "attempt_tamper_49_99_to_1_00",
        "amount": "1.00",
        "total_amount": "1.00",
        "price": "1.00",
        "currency": "EUR",
    }
    resp = client.post(
        f"/api/proposals/{sample_proposal.id}/checkout",
        json=tampered_payload,
        headers=headers,
    )
    assert resp.status_code in [200, 201]
    data = resp.json()

    # 3. Verify server-side authority
    assert Decimal(str(data["amount"])) == Decimal("49.99")
    assert data["currency"] == "USD"

    # 4. Verify internal DB order record is strictly $49.99
    order_uuid = uuid.UUID(data["order_id"]) if isinstance(data["order_id"], str) else data["order_id"]
    order = db.scalars(select(Order).where(Order.id == order_uuid)).first()
    assert order is not None
    assert order.amount == Decimal("49.99")
    assert order.currency == "USD"
    assert order.budget_reserved == Decimal("49.99")


def test_release_test_2_duplicate_order(client, test_user, sample_proposal, db):
    """
    MANDATORY TEST 2 — Duplicate order:
    Submit the same checkout operation repeatedly.
    Verify that duplicate requests do not create unintended PayPal orders.
    """
    headers = {"Authorization": f"Bearer {test_user.id}"}
    payload = {"checkout_attempt_id": "duplicate_attempt_key_abc"}

    # First checkout request
    resp1 = client.post(f"/api/proposals/{sample_proposal.id}/checkout", json=payload, headers=headers)
    assert resp1.status_code in [200, 201]
    res1_data = resp1.json()

    # Second identical checkout request
    resp2 = client.post(f"/api/proposals/{sample_proposal.id}/checkout", json=payload, headers=headers)
    assert resp2.status_code in [200, 201]
    res2_data = resp2.json()

    # Must return identical order IDs and PayPal order IDs
    assert res1_data["order_id"] == res2_data["order_id"]
    assert res1_data["paypal_order_id"] == res2_data["paypal_order_id"]

    # Verify DB has exactly 1 order for this proposal
    orders = db.scalars(select(Order).where(Order.proposal_id == sample_proposal.id)).all()
    assert len(orders) == 1


def test_release_test_3_approval_vs_capture(client, test_user, test_order, db):
    """
    MANDATORY TEST 3 — Approval versus capture:
    Approve a PayPal Sandbox order without capturing it.
    Verify that Carti does not display payment success.
    """
    # Simulate buyer onApprove in PayPal without capture
    test_order.status = "buyer_approved"
    db.commit()

    headers = {"Authorization": f"Bearer {test_user.id}"}
    resp = client.get(f"/api/orders/{test_order.id}", headers=headers)
    assert resp.status_code == 200
    receipt = resp.json()

    # Payment is NOT successful/completed
    assert receipt["status"] == "buyer_approved"
    assert receipt["status"] != "completed"
    assert receipt["paypal_capture_id"] is None
    assert receipt["captured_at"] is None


def test_release_test_4_confirmed_capture(client, test_user, test_order, db):
    """
    MANDATORY TEST 4 — Confirmed capture:
    Capture a valid Sandbox order.
    Retrieve the PayPal capture and verify the capture ID, actual amount, currency, and internal payment record.
    """
    headers = {"Authorization": f"Bearer {test_user.id}"}
    capture_resp = client.post(
        f"/api/orders/{test_order.id}/capture",
        json={"paypal_order_id": test_order.paypal_order_id},
        headers=headers,
    )
    assert capture_resp.status_code == 200
    cap_data = capture_resp.json()

    assert cap_data["status"] == "completed"
    assert cap_data["paypal_capture_id"].startswith("CAP-")
    assert Decimal(str(cap_data["amount"])) == test_order.amount
    assert cap_data["currency"] == test_order.currency
    assert cap_data["captured_at"] is not None

    # Retrieve receipt and verify internal DB consistency
    receipt_resp = client.get(f"/api/orders/{test_order.id}", headers=headers)
    assert receipt_resp.status_code == 200
    receipt = receipt_resp.json()
    assert receipt["status"] == "completed"
    assert receipt["paypal_capture_id"] == cap_data["paypal_capture_id"]
    assert Decimal(str(receipt["amount"])) == test_order.amount


def test_release_test_5_duplicate_capture(order_service, test_order, test_user, db):
    """
    MANDATORY TEST 5 — Duplicate capture:
    Submit capture twice, including concurrent attempts.
    Verify that the application does not produce duplicate captures or inconsistent internal records.
    """
    # 1. First capture succeeds
    c1 = order_service.capture_order(test_order.id, test_user.id)
    assert c1.status == "completed"
    first_cap_id = c1.paypal_capture_id

    # 2. Second capture is completely idempotent
    c2 = order_service.capture_order(test_order.id, test_user.id)
    assert c2.status == "completed"
    assert c2.paypal_capture_id == first_cap_id

    # 3. Concurrent capture attempts
    import concurrent.futures
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(order_service.capture_order, test_order.id, test_user.id)
        f2 = executor.submit(order_service.capture_order, test_order.id, test_user.id)
        results = [f1.result(), f2.result()]

    assert results[0].paypal_capture_id == first_cap_id
    assert results[1].paypal_capture_id == first_cap_id
    assert results[0].status == "completed"
    assert results[1].status == "completed"

    # Verify exactly 1 order in DB
    orders = db.scalars(select(Order).where(Order.id == test_order.id)).all()
    assert len(orders) == 1


def test_release_test_6_uncertain_capture(order_service, test_order, test_user, db, monkeypatch):
    """
    MANDATORY TEST 6 — Uncertain capture:
    Simulate a timeout after the provider may have processed capture.
    Verify that B10 reconciles the PayPal status before attempting another capture.
    """
    # 1. Simulate network timeout on capture call
    def mock_capture_timeout(*args, **kwargs):
        raise CartiAPIException(
            code=CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE,
            message="PayPal capture gateway timeout",
            status_code=504,
            retryable=True,
        )

    monkeypatch.setattr(paypal_service, "capture_order", mock_capture_timeout)

    with pytest.raises(CartiAPIException) as exc:
        order_service.capture_order(test_order.id, test_user.id)
    assert exc.value.code == CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE

    # Order remains uncompleted
    db.refresh(test_order)
    assert test_order.status != "completed"

    # 2. Simulate PayPal server-side completed state during reconciliation
    def mock_get_order(pp_order_id):
        return {
            "id": pp_order_id,
            "status": "COMPLETED",
            "purchase_units": [
                {
                    "payments": {
                        "captures": [{"id": "CAP-TIMEOUT-RECONCILED-888"}]
                    }
                }
            ],
        }

    monkeypatch.setattr(paypal_service, "get_order", mock_get_order)

    # 3. Reconciliation recovers the completed state safely without blind retry
    reconciled = order_service.reconcile_order_with_paypal(test_order.id, test_user.id)
    assert reconciled.status == "completed"
    assert reconciled.paypal_capture_id == "CAP-TIMEOUT-RECONCILED-888"

    # Subsequent capture returns completed order idempotently
    c_final = order_service.capture_order(test_order.id, test_user.id)
    assert c_final.status == "completed"


def test_release_test_7_refund_limit(order_service, test_user, active_mandate, sample_proposal, db):
    """
    MANDATORY TEST 7 — Refund limit:
    Capture $100 and attempt refunds totaling $120.
    Verify that the excess refund is rejected.
    """
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        paypal_order_id="PP-RELEASE-100",
        create_request_id="req_release_100",
        amount=Decimal("100.00"),
        currency="USD",
        status="completed",
        paypal_capture_id="CAP-RELEASE-100",
        captured_at=datetime.now(timezone.utc),
        budget_reserved=Decimal("0.00"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 1. Attempt $120 refund on $100 captured order -> rejected
    with pytest.raises(CartiAPIException) as exc1:
        order_service.refund_order(order.id, test_user.id, amount=Decimal("120.00"))
    assert exc1.value.code == CartiErrorCode.REFUND_NOT_ALLOWED
    assert exc1.value.status_code == 400

    # 2. Refund $60 -> succeeds
    ref1 = order_service.refund_order(order.id, test_user.id, amount=Decimal("60.00"))
    assert ref1.status == "completed"
    assert ref1.amount == Decimal("60.00")

    # 3. Attempt $50 refund (60 + 50 = 110 > 100) -> rejected
    with pytest.raises(CartiAPIException) as exc2:
        order_service.refund_order(order.id, test_user.id, amount=Decimal("50.00"))
    assert exc2.value.code == CartiErrorCode.REFUND_NOT_ALLOWED

    # 4. Refund remaining $40 (60 + 40 = 100) -> succeeds, order marked refunded
    ref2 = order_service.refund_order(order.id, test_user.id, amount=Decimal("40.00"))
    assert ref2.status == "completed"
    assert ref2.amount == Decimal("40.00")

    db.refresh(order)
    assert order.status == "refunded"


def test_release_test_8_cross_user_security(client, test_order, other_user):
    """
    MANDATORY TEST 8 — Cross-user security:
    User B attempts to capture and refund User A's order.
    Both attempts must be rejected.
    """
    headers = {"Authorization": f"Bearer {other_user.id}"}

    # User B attempts to capture User A's order
    res_cap = client.post(f"/api/orders/{test_order.id}/capture", headers=headers)
    assert res_cap.status_code == 403
    assert res_cap.json()["error"]["code"] == "ACCESS_DENIED"

    # User B attempts to refund User A's order
    res_ref = client.post(f"/api/orders/{test_order.id}/refund", headers=headers)
    assert res_ref.status_code == 403
    assert res_ref.json()["error"]["code"] == "ACCESS_DENIED"


def test_release_test_9_webhook_duplication(db, test_order, active_mandate):
    """
    MANDATORY TEST 9 — Webhook duplication:
    Deliver the same successful capture webhook multiple times.
    Verify that captured-spending accounting is updated exactly once.
    """
    webhook_svc = WebhookService(db)
    mandate_svc = MandateService(db)

    payload = {
        "id": "WH-DUP-CAPTURE-001",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {"id": test_order.paypal_order_id},
    }
    headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/cert.pem",
        "paypal-transmission-id": "trans-dup-001",
        "paypal-transmission-sig": "valid-sig",
        "paypal-transmission-time": datetime.now(timezone.utc).isoformat(),
    }

    # Delivery 1
    ok1, _ = webhook_svc.process_webhook(headers, b"{}", payload)
    assert ok1 is True

    breakdown1 = mandate_svc.calculate_available_budget(active_mandate.id)
    assert breakdown1.captured_spending == test_order.amount
    assert breakdown1.active_reservations == Decimal("0.00")

    # Delivery 2 & 3 (duplicate webhook redeliveries)
    ok2, _ = webhook_svc.process_webhook(headers, b"{}", payload)
    ok3, _ = webhook_svc.process_webhook(headers, b"{}", payload)
    assert ok2 is True
    assert ok3 is True

    # Spending accounting must NOT be multiplied
    breakdown2 = mandate_svc.calculate_available_budget(active_mandate.id)
    assert breakdown2.captured_spending == test_order.amount
    assert breakdown2.active_reservations == Decimal("0.00")


def test_release_test_10_payment_isolation(client, test_order):
    """
    MANDATORY TEST 10 — Payment isolation:
    Attempt to invoke PayPal order creation, capture, and refund from B5 or the frontend
    without the authorized B10 flow. Verify that all unauthorized attempts are rejected.
    """
    # 1. Verify B5 Agent Tools do not have payment, capture, or refund capabilities
    from server.app.agent.tools import (
        SearchProductsTool,
        GetProductTool,
        CompareCandidatesTool,
        ProposePurchaseTool,
    )
    b5_tools = [
        SearchProductsTool,
        GetProductTool,
        CompareCandidatesTool,
        ProposePurchaseTool,
    ]
    tool_names = [t.name for t in b5_tools]
    assert "paypal_checkout" not in tool_names
    assert "capture_payment" not in tool_names
    assert "refund_payment" not in tool_names
    assert "create_paypal_order" not in tool_names

    # 2. Frontend unauthenticated attempts to invoke payment operations
    res_cap_unauth = client.post(
        f"/api/orders/{test_order.id}/capture",
        headers={"Authorization": "Bearer invalid_or_expired_token"},
    )
    assert res_cap_unauth.status_code == 401
    assert res_cap_unauth.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    res_ref_unauth = client.post(
        f"/api/orders/{test_order.id}/refund",
        headers={"Authorization": "Bearer invalid_or_expired_token"},
    )
    assert res_ref_unauth.status_code == 401
    assert res_ref_unauth.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


# =====================================================================
# SECTION J: PAYPAL ERROR & FAILURE MODES (PHASES 2 & 3)
# =====================================================================

def test_paypal_client_invalid_credentials_handling(monkeypatch):
    """Test J1: 401 response from PayPal OAuth token acquisition raises PAYPAL_ORDER_FAILED."""
    svc = PayPalService()
    svc.client_id = "bad_client_id"
    svc.client_secret = "bad_secret"

    def mock_post_401(*args, **kwargs):
        request = httpx.Request("POST", "https://api.sandbox.paypal.com/v1/oauth2/token")
        response = httpx.Response(401, text='{"error":"invalid_client"}', request=request)
        raise httpx.HTTPStatusError("Unauthorized", request=request, response=response)

    monkeypatch.setattr(httpx.Client, "post", mock_post_401)

    with pytest.raises(CartiAPIException) as exc:
        svc.get_access_token()
    assert exc.value.code == CartiErrorCode.PAYPAL_ORDER_FAILED
    assert exc.value.status_code == 401


def test_paypal_client_rate_limited_handling(monkeypatch):
    """Test J2: 429 response from PayPal API raises DOWNSTREAM_SERVICE_UNAVAILABLE or 429."""
    svc = PayPalService()
    svc.client_id = "real_mock_client_id"
    svc.client_secret = "real_mock_client_secret"
    svc._cached_token = "valid_cached_token"
    svc._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    def mock_get_429(*args, **kwargs):
        request = httpx.Request("GET", "https://api.sandbox.paypal.com/v2/checkout/orders/123")
        response = httpx.Response(429, text='{"error":"rate_limited"}', request=request)
        raise httpx.HTTPStatusError("Rate limited", request=request, response=response)

    monkeypatch.setattr(httpx.Client, "get", mock_get_429)

    with pytest.raises(CartiAPIException) as exc:
        svc.get_order("PP-ORDER-123")
    assert exc.value.status_code == 429


def test_paypal_token_expiry_triggers_refresh(monkeypatch):
    """Test J3: Expired token in cache triggers fresh token acquisition."""
    svc = PayPalService()
    svc.client_id = "real_mock_client_id"
    svc.client_secret = "real_mock_client_secret"
    svc._cached_token = "stale_token"
    svc._token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    def mock_post_fresh(*args, **kwargs):
        request = httpx.Request("POST", "https://api.sandbox.paypal.com/v1/oauth2/token")
        return httpx.Response(200, json={"access_token": "fresh_refreshed_token", "expires_in": 3600}, request=request)

    monkeypatch.setattr(httpx.Client, "post", mock_post_fresh)

    fresh_token = svc.get_access_token()
    assert fresh_token == "fresh_refreshed_token"
    assert svc._cached_token == "fresh_refreshed_token"

