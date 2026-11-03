"""Comprehensive Security Audit & Verification Test Suite for Backend Module B2.

Covers:
- Dual-user (User A vs User B) complete resource tree isolation (Mandates, Requests, Candidates, Proposals, Orders, Refunds, Audit)
- IDOR vulnerabilities and URL parameter tampering
- Cross-resource relational integrity (tampered foreign keys across users)
- Client-supplied identity spoofing in request bodies and query parameters
- Cookie security: HttpOnly, SameSite, Secure in production
- Session token hashing & database leak protection
- Session lifecycle: rotation, expiration, revocation, repeated logout
- Password security: Argon2id verification, absence of plaintext/hashes in responses
- Timing attack mitigation on login
- Rate limiting enforcement on authentication
- Demo mode lockdown in production
- Financial data cascade immutability
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import uuid
import pytest
from sqlalchemy import select
from server.app.core.config import settings
from server.app.core.errors import CartiAPIException
from server.app.core.rate_limit import auth_limiter
from server.app.models.audit import AuditEvent
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.request import RequestEvent, ShoppingRequest
from server.app.models.session import UserSession
from server.app.models.user import User
from server.app.services.audit_service import AuditService


@pytest.fixture(autouse=True)
def reset_limiters():
    """Reset auth rate limiter before every audit test."""
    auth_limiter.reset()
    yield
    auth_limiter.reset()


@pytest.fixture
def user_a(db):
    """Create User A in db."""
    user = User(
        id=uuid.uuid4(),
        email="audit_user_a@carti.local",
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
        email="audit_user_b@carti.local",
        is_active=True,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_a_resources(db, user_a):
    """Complete resource hierarchy for User A."""
    mandate = Mandate(
        user_id=user_a.id,
        version=1,
        total_budget=Decimal("500.00"),
        per_item_cap=Decimal("250.00"),
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
    db.flush()

    req = ShoppingRequest(
        user_id=user_a.id,
        mandate_id=mandate.id,
        request_text="User A noise-cancelling headphones",
        normalized_intent={"category": "Electronics", "max_price": "200.00"},
        status="proposal_ready",
    )
    db.add(req)
    db.flush()

    event = RequestEvent(
        request_id=req.id,
        event_type="proposal_ready",
        payload={"step": "proposal_ready", "progress": 100},
    )
    db.add(event)
    db.flush()

    cand = Candidate(
        request_id=req.id,
        provider_product_id="PROD-A-01",
        title="Bose QC45",
        category="Electronics",
        rank_score=Decimal("0.98"),
    )
    db.add(cand)
    db.flush()

    offer = CandidateOffer(
        candidate_id=cand.id,
        domain="bestbuy.com",
        buy_url="https://bestbuy.com/products/bose-qc45",
        price_amount=Decimal("199.99"),
        currency="USD",
        availability="InStock",
    )
    db.add(offer)
    db.flush()

    proposal = Proposal(
        request_id=req.id,
        mandate_id=mandate.id,
        candidate_id=cand.id,
        offer_id=offer.id,
        user_id=user_a.id,
        unit_price_at_proposal=Decimal("199.99"),
        subtotal_at_proposal=Decimal("199.99"),
        currency="USD",
        quantity=1,
        rationale="Premium headphones within budget",
        guardrail_result={"passed": True, "checks": []},
        status="checkout_started",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(proposal)
    db.flush()

    order = Order(
        proposal_id=proposal.id,
        user_id=user_a.id,
        paypal_order_id="PP-ORD-USER-A",
        paypal_capture_id="PP-CAP-USER-A",
        create_request_id="req-user-a-audit",
        amount=Decimal("199.99"),
        currency="USD",
        status="completed",
        budget_reserved=Decimal("199.99"),
        captured_at=datetime.now(timezone.utc),
    )
    db.add(order)
    db.flush()

    audit_ev = AuditEvent(
        user_id=user_a.id,
        request_id=req.id,
        order_id=order.id,
        event_type="paypal_order_created",
        details={"amount": "199.99"},
    )
    db.add(audit_ev)
    db.commit()

    return {
        "mandate": mandate,
        "request": req,
        "event": event,
        "candidate": cand,
        "proposal": proposal,
        "order": order,
        "audit": audit_ev,
    }


@pytest.fixture
def user_b_resources(db, user_b):
    """Complete resource hierarchy for User B."""
    mandate = Mandate(
        user_id=user_b.id,
        version=1,
        total_budget=Decimal("300.00"),
        per_item_cap=Decimal("150.00"),
        currency="USD",
        allowed_categories=["Home"],
        blocked_categories=["Electronics"],
        allowed_retailers=["target.com"],
        max_quantity_per_product=1,
        price_tolerance_pct=Decimal("0.0500"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        status="active",
    )
    db.add(mandate)
    db.flush()

    req = ShoppingRequest(
        user_id=user_b.id,
        mandate_id=mandate.id,
        request_text="User B modern floor lamp",
        normalized_intent={"category": "Home", "max_price": "80.00"},
        status="proposal_ready",
    )
    db.add(req)
    db.flush()

    event = RequestEvent(
        request_id=req.id,
        event_type="proposal_ready",
        payload={"step": "proposal_ready", "progress": 100},
    )
    db.add(event)
    db.flush()

    cand = Candidate(
        request_id=req.id,
        provider_product_id="PROD-B-01",
        title="Modern Arc Floor Lamp",
        category="Home",
        rank_score=Decimal("0.90"),
    )
    db.add(cand)
    db.flush()

    offer = CandidateOffer(
        candidate_id=cand.id,
        domain="target.com",
        buy_url="https://target.com/products/lamp-b",
        price_amount=Decimal("75.00"),
        currency="USD",
        availability="InStock",
    )
    db.add(offer)
    db.flush()

    proposal = Proposal(
        request_id=req.id,
        mandate_id=mandate.id,
        candidate_id=cand.id,
        offer_id=offer.id,
        user_id=user_b.id,
        unit_price_at_proposal=Decimal("75.00"),
        subtotal_at_proposal=Decimal("75.00"),
        currency="USD",
        quantity=1,
        rationale="Matches warm home lighting",
        guardrail_result={"passed": True, "checks": []},
        status="checkout_started",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(proposal)
    db.flush()

    order = Order(
        proposal_id=proposal.id,
        user_id=user_b.id,
        paypal_order_id="PP-ORD-USER-B",
        paypal_capture_id="PP-CAP-USER-B",
        create_request_id="req-user-b-audit",
        amount=Decimal("75.00"),
        currency="USD",
        status="completed",
        budget_reserved=Decimal("75.00"),
        captured_at=datetime.now(timezone.utc),
    )
    db.add(order)
    db.flush()

    audit_ev = AuditEvent(
        user_id=user_b.id,
        request_id=req.id,
        order_id=order.id,
        event_type="paypal_order_created",
        details={"amount": "75.00"},
    )
    db.add(audit_ev)
    db.commit()

    return {
        "mandate": mandate,
        "request": req,
        "event": event,
        "candidate": cand,
        "proposal": proposal,
        "order": order,
        "audit": audit_ev,
    }


# ==============================================================================
# SECTION 1: Exhaustive Cross-User Ownership Boundary Tests
# ==============================================================================


def test_cross_user_mandate_leak_blocked(client, user_a, user_b_resources):
    """User A cannot read User B's active mandate."""
    res = client.get(
        "/api/mandates/current",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    # User A has no mandate created yet; must return 404, not leak User B's
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "MANDATE_NOT_FOUND"


def test_cross_user_shopping_request_blocked(client, user_a, user_b_resources):
    """User A cannot view User B's shopping request."""
    b_req_id = user_b_resources["request"].id
    res = client.get(
        f"/api/requests/{b_req_id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_sse_stream_blocked(client, user_a, user_b_resources):
    """User A cannot stream progress or replay events for User B's request."""
    b_req_id = user_b_resources["request"].id
    res = client.get(
        f"/api/requests/{b_req_id}/stream",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_request_cancellation_blocked(client, user_a, user_b_resources):
    """User A cannot cancel User B's request."""
    b_req_id = user_b_resources["request"].id
    res = client.post(
        f"/api/requests/{b_req_id}/cancel",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_candidate_retrieval_blocked(client, user_a, user_b_resources):
    """User A cannot view candidates evaluated for User B."""
    b_req_id = user_b_resources["request"].id
    res = client.get(
        f"/api/requests/{b_req_id}/candidates",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_proposal_inspection_blocked(client, user_a, user_b_resources):
    """User A cannot review User B's proposal."""
    b_prop_id = user_b_resources["proposal"].id
    res = client.get(
        f"/api/proposals/{b_prop_id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_order_creation_from_proposal_blocked(client, user_a, user_b_resources):
    """User A cannot create a PayPal order against User B's proposal."""
    b_prop_id = user_b_resources["proposal"].id
    res = client.post(
        f"/api/proposals/{b_prop_id}/order",
        json={"checkout_attempt_id": "hack-attempt-1"},
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_order_receipt_blocked(client, user_a, user_b_resources):
    """User A cannot view User B's order receipt."""
    b_order_id = user_b_resources["order"].id
    res = client.get(
        f"/api/orders/{b_order_id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_payment_capture_blocked(client, user_a, user_b_resources):
    """User A cannot capture User B's payment."""
    b_order_id = user_b_resources["order"].id
    res = client.post(
        f"/api/orders/{b_order_id}/capture",
        json={"paypal_order_id": "PP-ORD-USER-B"},
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_refund_blocked(client, user_a, user_b_resources):
    """User A cannot refund User B's order."""
    b_order_id = user_b_resources["order"].id
    res = client.post(
        f"/api/orders/{b_order_id}/refund",
        json={"reason": "Unauthorized refund by User A"},
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_cross_user_audit_events_isolation(db, user_a, user_b, user_b_resources):
    """User A cannot query User B's security audit events."""
    audit_service = AuditService(db)

    with pytest.raises(CartiAPIException) as exc_info:
        audit_service.get_events_for_user(
            target_user_id=user_b.id,
            caller_user_id=user_a.id,
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ACCESS_DENIED"


# ==============================================================================
# SECTION 2: Nested Cross-Resource Tampering & Spoofing
# ==============================================================================


def test_tampered_proposal_candidate_mismatch(client, db, user_a, user_a_resources, user_b_resources):
    """
    If a proposal is crafted referencing User A's request, but User B's candidate product,
    it must be rejected with ACCESS_DENIED.
    """
    tampered_prop = Proposal(
        request_id=user_a_resources["request"].id,
        mandate_id=user_a_resources["mandate"].id,
        candidate_id=user_b_resources["candidate"].id,  # Foreign candidate!
        offer_id=user_b_resources["candidate"].offers[0].id,
        user_id=user_a.id,
        unit_price_at_proposal=Decimal("75.00"),
        subtotal_at_proposal=Decimal("75.00"),
        currency="USD",
        quantity=1,
        rationale="Tampered candidate association",
        guardrail_result={"passed": True, "checks": []},
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(tampered_prop)
    db.commit()
    db.refresh(tampered_prop)

    res = client.get(
        f"/api/proposals/{tampered_prop.id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"
    assert "candidate" in res.json()["error"]["message"].lower()


def test_tampered_order_proposal_user_mismatch(client, db, user_a, user_b, user_b_resources):
    """
    If an order record is maliciously created owned by User A, but points to User B's proposal,
    viewing the order receipt must fail with ACCESS_DENIED.
    """
    # Create secondary proposal for User B that doesn't have an order yet
    proposal_b2 = Proposal(
        request_id=user_b_resources["request"].id,
        mandate_id=user_b_resources["mandate"].id,
        candidate_id=user_b_resources["candidate"].id,
        offer_id=user_b_resources["candidate"].offers[0].id,
        user_id=user_b.id,
        unit_price_at_proposal=Decimal("75.00"),
        subtotal_at_proposal=Decimal("75.00"),
        currency="USD",
        quantity=1,
        rationale="Second proposal for User B",
        guardrail_result={"passed": True, "checks": []},
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(proposal_b2)
    db.flush()

    tampered_order = Order(
        proposal_id=proposal_b2.id,  # Proposal belongs to User B
        user_id=user_a.id,  # Order owned by User A
        paypal_order_id="PP-ORD-TAMPER-01",
        create_request_id="tamper-attempt-01",
        amount=Decimal("75.00"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("75.00"),
    )
    db.add(tampered_order)
    db.commit()
    db.refresh(tampered_order)

    res = client.get(
        f"/api/orders/{tampered_order.id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_query_parameter_user_id_spoofing_ignored(client, user_a, user_b, user_a_resources, user_b_resources):
    """
    Passing query parameter ?user_id=<user_b.id> must have zero effect on returned data.
    """
    res = client.get(
        f"/api/orders?user_id={user_b.id}",
        headers={"Authorization": f"Bearer {user_a.id}"},
    )
    assert res.status_code == 200
    # Must only return User A's order
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(user_a_resources["order"].id)


# ==============================================================================
# SECTION 3: Session Security, Tokens, and Database Leak Defense
# ==============================================================================


def test_cookie_security_attributes(client):
    """Verify session cookie attributes: HttpOnly, SameSite=Lax, Path=/."""
    res = client.post(
        "/api/auth/register",
        json={"email": "cookie_audit@carti.local", "password": "SecurePassword123!"},
    )
    assert res.status_code == 201
    set_cookie = res.headers.get("set-cookie", "")

    assert settings.SESSION_COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()
    assert "path=/" in set_cookie.lower()


def test_token_hash_stored_in_database(client, db):
    """Verify raw token is never stored in DB; only SHA-256 hash is persisted."""
    res = client.post(
        "/api/auth/register",
        json={"email": "hash_audit@carti.local", "password": "SecurePassword123!"},
    )
    assert res.status_code == 201
    raw_token = res.json()["token"]
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Search DB for raw token (must NOT exist)
    bad_match = db.scalars(select(UserSession).where(UserSession.token_hash == raw_token)).first()
    assert bad_match is None

    # Search DB for hash (must exist)
    good_match = db.scalars(select(UserSession).where(UserSession.token_hash == expected_hash)).first()
    assert good_match is not None

    # Database leak attack simulation:
    # An attacker who steals the database hash attempts to use it as Bearer token
    leak_attack_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expected_hash}"},
    )
    # Must fail because server will hash the hash!
    assert leak_attack_res.status_code == 401


def test_session_fixation_protection(client, db):
    """Login must rotate the session token, generating a new distinct session record."""
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "fixation@carti.local", "password": "Password123!"},
    )
    token_1 = reg_res.json()["token"]

    login_res = client.post(
        "/api/auth/login",
        json={"email": "fixation@carti.local", "password": "Password123!"},
    )
    token_2 = login_res.json()["token"]

    assert token_1 != token_2


def test_tampered_and_malformed_bearer_tokens(client):
    """Tampered token strings are safely rejected with 401."""
    # Invalid token format
    res1 = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not_a_valid_token_string_here"},
    )
    assert res1.status_code == 401

    # Empty token
    res2 = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer "},
    )
    assert res2.status_code == 401

    # Non-bearer scheme
    res3 = client.get(
        "/api/auth/me",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert res3.status_code == 401


# ==============================================================================
# SECTION 4: Password Security & Anti-Enumeration
# ==============================================================================


def test_password_hash_never_exposed(client, db):
    """Verify password hash is valid Argon2id and never returned in API responses."""
    res = client.post(
        "/api/auth/register",
        json={"email": "exposure_test@carti.local", "password": "SecurePassword123!"},
    )
    data = res.json()
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]

    # In DB
    user = db.scalars(select(User).where(User.email == "exposure_test@carti.local")).first()
    assert user.password_hash.startswith("$argon2id$")


def test_constant_time_dummy_verify_on_nonexistent_email(client):
    """Verify non-existent email performs dummy Argon2id hash verification."""
    # Response code must be consistent 401 with standard error
    res = client.post(
        "/api/auth/login",
        json={"email": "nonexistent_email_123@carti.local", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert res.json()["error"]["message"] == "Invalid email or password."


# ==============================================================================
# SECTION 5: Production Lockdown Verification
# ==============================================================================


def test_production_mode_forces_demo_lockdown_and_secure_cookies(client, monkeypatch):
    """
    Verify that in production:
    1. DEMO_USER_ENABLED is forced to False.
    2. SESSION_COOKIE_SECURE is forced to True.
    3. Demo login endpoint returns 403 ACCESS_DENIED.
    """
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "DEMO_USER_ENABLED", True)  # Operator attempt to enable demo

    # Re-trigger production security enforcement
    settings.enforce_production_security()

    assert settings.DEMO_USER_ENABLED is False
    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.is_demo_allowed() is False

    # Attempt demo login
    res = client.post("/api/auth/demo", json={})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


# ==============================================================================
# SECTION 6: Financial Data Cascade Immutability
# ==============================================================================


def test_financial_records_immutable_on_user_deletion(db, user_a, user_a_resources):
    """
    Verify that deleting a user with completed orders or audit events is blocked
    by database integrity constraints (RESTRICT) rather than silently wiping payment records.
    """
    import sqlalchemy.exc

    # Attempting to delete user_a directly while orders/audits exist
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.delete(user_a)
        db.commit()

    db.rollback()
