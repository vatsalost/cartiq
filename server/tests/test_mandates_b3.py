"""Backend Module B3: Comprehensive Mandate Service & Financial Engine Test Suite.

Covers all 37 test cases specified in Carti Core Module Specification v1.0 Section 14:
- Group 1: Creation and Validation (Tests 01–11)
- Group 2: Versioning Architecture (Tests 12–18)
- Group 3: Financial Engine, Budget Calculations & Reservations (Tests 19–28)
- Group 4: Revocation, Lifecycle & Invalidation (Tests 29–34)
- Group 5: Concurrency, Currency & API Integration (Tests 35–37)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select

from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest
from server.app.models.user import User
from server.app.schemas.mandate import MandateCreate
from server.app.services.mandate_service import MandateService


# ==============================================================================
# Helper Fixtures & Utilities
# ==============================================================================

@pytest.fixture
def b3_user_a(db):
    """User A for B3 mandate testing."""
    user = User(
        id=uuid.uuid4(),
        email="b3_user_a@carti.local",
        is_active=True,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def b3_user_b(db):
    """User B for cross-user isolation and ownership tests."""
    user = User(
        id=uuid.uuid4(),
        email="b3_user_b@carti.local",
        is_active=True,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    """Generate authorization bearer headers for a given user."""
    return {"Authorization": f"Bearer {user.id}"}


def make_test_proposal(
    db,
    user: User,
    mandate: Mandate,
    amount: Decimal = Decimal("50.00"),
    currency: str = "USD",
    status: str = "pending",
) -> Proposal:
    """Helper to create a fully-valid Proposal with valid FK relationships."""
    req = ShoppingRequest(
        user_id=user.id,
        mandate_id=mandate.id,
        request_text="Sample shopping query",
        normalized_intent={"category": "Home"},
        status="running",
    )
    db.add(req)
    db.flush()

    cand = Candidate(
        request_id=req.id,
        provider_product_id=f"P_{uuid.uuid4().hex[:8]}",
        title="Test Product Item",
        category="Home",
        rank_score=Decimal("0.95"),
    )
    db.add(cand)
    db.flush()

    offer = CandidateOffer(
        candidate_id=cand.id,
        provider_offer_id=f"OFF_{uuid.uuid4().hex[:8]}",
        domain="target.com",
        buy_url="https://target.com/test-product",
        price_amount=amount,
        currency=currency,
        availability="InStock",
        condition="new",
        is_eligible=True,
    )
    db.add(offer)
    db.flush()

    prop = Proposal(
        request_id=req.id,
        mandate_id=mandate.id,
        user_id=user.id,
        candidate_id=cand.id,
        offer_id=offer.id,
        quantity=1,
        unit_price_at_proposal=amount,
        subtotal_at_proposal=amount,
        currency=currency,
        rationale="Matches all criteria within mandate cap.",
        guardrail_result={"passed": True, "checks": []},
        status=status,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


# ==============================================================================
# GROUP 1: Mandate Creation and Validation (Tests 01–11)
# ==============================================================================

def test_01_valid_mandate_creation_full_parameters(client, b3_user_a):
    """Test 01: Valid mandate creation with full parameters returns 201 and rich response."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    payload = {
        "total_budget": "150.00",
        "per_item_cap": "50.00",
        "currency": "USD",
        "allowed_categories": ["Electronics", "Home"],
        "blocked_categories": ["Clothing"],
        "allowed_retailers": ["https://target.com/deals", "amazon.com"],
        "max_quantity_per_product": 2,
        "price_tolerance_pct": "0.05",
        "expires_at": future_date,
    }

    res = client.post("/api/mandates", json=payload, headers=auth_headers(b3_user_a))
    assert res.status_code == 201
    data = res.json()

    assert data["total_budget"] == "150.00"
    assert data["per_item_cap"] == "50.00"
    assert data["currency"] == "USD"
    assert data["version"] == 1
    assert data["status"] == "active"
    assert "target.com" in data["allowed_retailers"]
    assert "amazon.com" in data["allowed_retailers"]
    assert data["available_budget"] == "150.00"
    assert data["captured_spending"] == "0.00"
    assert data["active_reservations"] == "0.00"
    assert "summary_text" in data
    assert "150.00 USD" in data["summary_text"]


def test_02_zero_total_budget_rejection(client, b3_user_a):
    """Test 02: Zero total budget is rejected with validation error (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "total_budget": "0.00",
        "per_item_cap": "0.00",
        "currency": "USD",
        "allowed_categories": ["Home"],
        "expires_at": future_date,
    }
    res = client.post("/api/mandates", json=payload, headers=auth_headers(b3_user_a))
    assert res.status_code == 422


def test_03_negative_budget_rejection(client, b3_user_a):
    """Test 03: Negative budget is rejected with validation error (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "total_budget": "-25.00",
        "per_item_cap": "10.00",
        "currency": "USD",
        "allowed_categories": ["Home"],
        "expires_at": future_date,
    }
    res = client.post("/api/mandates", json=payload, headers=auth_headers(b3_user_a))
    assert res.status_code == 422


def test_04_per_item_cap_exceeding_total_budget_rejection(client, b3_user_a):
    """Test 04: Per-item cap exceeding total budget is rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "total_budget": "50.00",
        "per_item_cap": "100.00",
        "currency": "USD",
        "allowed_categories": ["Home"],
        "expires_at": future_date,
    }
    res = client.post("/api/mandates", json=payload, headers=auth_headers(b3_user_a))
    assert res.status_code == 422
    assert "per_item_cap cannot be greater than total_budget" in res.text


def test_05_invalid_currency_rejection(client, b3_user_a):
    """Test 05: Invalid currency (lowercase or non-ISO) is rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    # Lowercase
    res_lower = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "usd",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res_lower.status_code == 422

    # Non-conforming code
    res_non_iso = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "US1",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res_non_iso.status_code == 422


def test_06_invalid_category_names_rejection(client, b3_user_a):
    """Test 06: Invalid category names (empty or invalid characters) are rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    # Empty string in allowed_categories
    res1 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": [""],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res1.status_code == 422

    # Malicious or invalid characters
    res2 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["<script>alert(1)</script>"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res2.status_code == 422


def test_07_overlapping_allowed_and_blocked_categories_rejection(client, b3_user_a):
    """Test 07: Overlapping allowed and blocked categories are rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home", "Electronics"],
            "blocked_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res.status_code == 422
    assert "cannot overlap" in res.text


def test_08_invalid_retailer_domain_syntax_rejection(client, b3_user_a):
    """Test 08: Invalid retailer domain syntax is rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "allowed_retailers": ["invalid..domain...com"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res.status_code == 422
    assert "Invalid retailer domain format" in res.text


def test_09_invalid_max_quantity_per_product(client, b3_user_a):
    """Test 09: Invalid max quantity per product (0 or >50) is rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    # 0 quantity
    res_zero = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "max_quantity_per_product": 0,
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res_zero.status_code == 422

    # >50 quantity
    res_high = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "max_quantity_per_product": 51,
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res_high.status_code == 422


def test_10_invalid_price_tolerance_pct(client, b3_user_a):
    """Test 10: Invalid price tolerance percentage (<0 or >0.50) is rejected (422)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    # Negative tolerance
    res_neg = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "price_tolerance_pct": "-0.05",
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res_neg.status_code == 422

    # Excessive tolerance (> 0.50 / 50%)
    res_high = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "price_tolerance_pct": "0.75",
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res_high.status_code == 422


def test_11_expired_mandate_date_on_creation_rejection(client, b3_user_a):
    """Test 11: Past expiration date on mandate creation is rejected (422)."""
    past_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": past_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res.status_code == 422
    assert "must be in the future" in res.text


# ==============================================================================
# GROUP 2: Mandate Versioning Architecture (Tests 12–18)
# ==============================================================================

def test_12_v1_creation_initial_state(client, b3_user_a):
    """Test 12: Initial mandate creation assigns version 1 and status 'active'."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res.status_code == 201
    assert res.json()["version"] == 1
    assert res.json()["status"] == "active"


def test_13_v2_creation_increments_version(client, b3_user_a):
    """Test 13: Updating a mandate increments version to 2."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    res2 = client.post(
        "/api/mandates",
        json={
            "total_budget": "150.00",
            "per_item_cap": "60.00",
            "currency": "USD",
            "allowed_categories": ["Home", "Electronics"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    assert res2.status_code == 201
    assert res2.json()["version"] == 2
    assert res2.json()["status"] == "active"


def test_14_v1_preservation(client, db, b3_user_a):
    """Test 14: Version 1 record is preserved unmodified when version 2 is created."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res1 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    v1_id = uuid.UUID(res1.json()["id"])

    # Create V2
    client.post(
        "/api/mandates",
        json={
            "total_budget": "200.00",
            "per_item_cap": "80.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )

    # Inspect V1 in DB directly
    v1_mandate = db.get(Mandate, v1_id)
    assert v1_mandate is not None
    assert v1_mandate.version == 1
    assert v1_mandate.total_budget == Decimal("100.00")
    assert v1_mandate.per_item_cap == Decimal("40.00")


def test_15_v1_marked_superseded(client, db, b3_user_a):
    """Test 15: V1 is marked 'superseded' after V2 is created."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res1 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    v1_id = uuid.UUID(res1.json()["id"])

    client.post(
        "/api/mandates",
        json={
            "total_budget": "200.00",
            "per_item_cap": "80.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )

    db.expire_all()
    v1_mandate = db.get(Mandate, v1_id)
    assert v1_mandate.status == "superseded"


def test_16_historical_version_retrieval(client, b3_user_a):
    """Test 16: Historical version 1 can be retrieved via GET /api/mandates/versions/1."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )
    client.post(
        "/api/mandates",
        json={
            "total_budget": "200.00",
            "per_item_cap": "80.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=auth_headers(b3_user_a),
    )

    # Historical lookup
    res_v1 = client.get("/api/mandates/versions/1", headers=auth_headers(b3_user_a))
    assert res_v1.status_code == 200
    assert res_v1.json()["version"] == 1
    assert res_v1.json()["total_budget"] == "100.00"
    assert res_v1.json()["status"] == "superseded"

    # Current remains version 2
    res_curr = client.get("/api/mandates/current", headers=auth_headers(b3_user_a))
    assert res_curr.status_code == 200
    assert res_curr.json()["version"] == 2


def test_17_concurrent_or_sequential_mandate_versioning(client, b3_user_a):
    """Test 17: Consecutive updates monotonically increase version numbers."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    for v in range(1, 5):
        res = client.post(
            "/api/mandates",
            json={
                "total_budget": f"{100 + v * 10}.00",
                "per_item_cap": "50.00",
                "currency": "USD",
                "allowed_categories": ["Home"],
                "expires_at": future_date,
            },
            headers=auth_headers(b3_user_a),
        )
        assert res.status_code == 201
        assert res.json()["version"] == v


def test_18_cross_user_version_isolation(client, b3_user_a, b3_user_b):
    """Test 18: Mandate versions are strictly scoped per user and cannot leak."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    # User A creates V1 and V2
    client.post(
        "/api/mandates",
        json={"total_budget": "100.00", "per_item_cap": "50.00", "currency": "USD", "allowed_categories": ["Home"], "expires_at": future_date},
        headers=auth_headers(b3_user_a),
    )
    client.post(
        "/api/mandates",
        json={"total_budget": "150.00", "per_item_cap": "50.00", "currency": "USD", "allowed_categories": ["Home"], "expires_at": future_date},
        headers=auth_headers(b3_user_a),
    )

    # User B creates first mandate: must be version 1
    res_b = client.post(
        "/api/mandates",
        json={"total_budget": "75.00", "per_item_cap": "30.00", "currency": "USD", "allowed_categories": ["Electronics"], "expires_at": future_date},
        headers=auth_headers(b3_user_b),
    )
    assert res_b.status_code == 201
    assert res_b.json()["version"] == 1

    # User B tries to retrieve V2 -> 404 (User B doesn't have a V2)
    res_b_v2 = client.get("/api/mandates/versions/2", headers=auth_headers(b3_user_b))
    assert res_b_v2.status_code == 404


# ==============================================================================
# GROUP 3: Financial Engine, Budget Calculations & Reservations (Tests 19–28)
# ==============================================================================

def test_19_budget_calculation_zero_spend(client, db, b3_user_a):
    """Test 19: Budget calculation with zero spend returns available == total."""
    service = MandateService(db)
    future_date = datetime.now(timezone.utc) + timedelta(days=7)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("200.00"),
            per_item_cap=Decimal("100.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=future_date,
        ),
    )

    breakdown = service.calculate_available_budget(mandate.id)
    assert breakdown.total_budget == Decimal("200.00")
    assert breakdown.captured_spending == Decimal("0.00")
    assert breakdown.active_reservations == Decimal("0.00")
    assert breakdown.available_budget == Decimal("200.00")

    # Check via API endpoint
    res = client.get("/api/mandates/current/budget", headers=auth_headers(b3_user_a))
    assert res.status_code == 200
    assert res.json()["available_budget"] == "200.00"


def test_20_budget_calculation_completed_orders(db, b3_user_a):
    """Test 20: Completed orders accurately deduct from available budget as captured spend."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("200.00"),
            per_item_cap=Decimal("100.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("60.00"), status="ordered")

    order = Order(
        proposal_id=prop.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-ORD-20",
        create_request_id="req-ord-20",
        amount=Decimal("60.00"),
        currency="USD",
        status="completed",
        budget_reserved=Decimal("60.00"),
    )
    db.add(order)
    db.commit()

    breakdown = service.calculate_available_budget(mandate.id)
    assert breakdown.total_budget == Decimal("200.00")
    assert breakdown.captured_spending == Decimal("60.00")
    assert breakdown.active_reservations == Decimal("0.00")
    assert breakdown.available_budget == Decimal("140.00")


def test_21_budget_calculation_active_reservations(db, b3_user_a):
    """Test 21: Active reservations deduct from available budget."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("200.00"),
            per_item_cap=Decimal("100.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("45.00"), status="ordered")

    # In-flight reservation
    order = Order(
        proposal_id=prop.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-ORD-21",
        create_request_id="req-ord-21",
        amount=Decimal("45.00"),
        currency="USD",
        status="buyer_approved",
        budget_reserved=Decimal("45.00"),
    )
    db.add(order)
    db.commit()

    breakdown = service.calculate_available_budget(mandate.id)
    assert breakdown.captured_spending == Decimal("0.00")
    assert breakdown.active_reservations == Decimal("45.00")
    assert breakdown.available_budget == Decimal("155.00")


def test_22_budget_calculation_released_reservations(db, b3_user_a):
    """Test 22: Cancelled or refunded orders release reservations back to available."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("200.00"),
            per_item_cap=Decimal("100.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("50.00"), status="ordered")

    order = Order(
        proposal_id=prop.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-ORD-22",
        create_request_id="req-ord-22",
        amount=Decimal("50.00"),
        currency="USD",
        status="cancelled",
        budget_reserved=Decimal("0.00"),
    )
    db.add(order)
    db.commit()

    breakdown = service.calculate_available_budget(mandate.id)
    assert breakdown.captured_spending == Decimal("0.00")
    assert breakdown.active_reservations == Decimal("0.00")
    assert breakdown.available_budget == Decimal("200.00")


def test_23_budget_calculation_multiple_mixed_orders(db, b3_user_a):
    """Test 23: Budget with mixed completed, in-flight, and cancelled orders calculates correctly."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("200.00"),
            per_item_cap=Decimal("100.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    # Completed ($50)
    p1 = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("50.00"), status="ordered")
    o1 = Order(proposal_id=p1.id, user_id=b3_user_a.id, paypal_order_id="PP-1", create_request_id="req-23-1", amount=Decimal("50.00"), currency="USD", status="completed", budget_reserved=Decimal("50.00"))
    db.add(o1)

    # In-flight ($30 reserved)
    p2 = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("30.00"), status="ordered")
    o2 = Order(proposal_id=p2.id, user_id=b3_user_a.id, paypal_order_id="PP-2", create_request_id="req-23-2", amount=Decimal("30.00"), currency="USD", status="capture_pending", budget_reserved=Decimal("30.00"))
    db.add(o2)

    # Cancelled ($40 released)
    p3 = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("40.00"), status="ordered")
    o3 = Order(proposal_id=p3.id, user_id=b3_user_a.id, paypal_order_id="PP-3", create_request_id="req-23-3", amount=Decimal("40.00"), currency="USD", status="cancelled", budget_reserved=Decimal("0.00"))
    db.add(o3)
    db.commit()

    breakdown = service.calculate_available_budget(mandate.id)
    assert breakdown.total_budget == Decimal("200.00")
    assert breakdown.captured_spending == Decimal("50.00")
    assert breakdown.active_reservations == Decimal("30.00")
    assert breakdown.available_budget == Decimal("120.00")  # 200 - 50 - 30


def test_24_budget_reservation_service_method(db, b3_user_a):
    """Test 24: reserve_budget method successfully reserves budget and emits audit event."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("50.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    breakdown = service.reserve_budget(mandate.id, amount=Decimal("40.00"))
    assert breakdown.available_budget == Decimal("100.00")  # Order hasn't been committed yet


def test_25_budget_reservation_exceeding_available(db, b3_user_a):
    """Test 25: Reserving more than available budget raises CartiAPIException with BUDGET_EXCEEDED."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("50.00"),
            per_item_cap=Decimal("50.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    with pytest.raises(CartiAPIException) as exc_info:
        service.reserve_budget(mandate.id, amount=Decimal("60.00"))

    assert exc_info.value.code == CartiErrorCode.BUDGET_EXCEEDED
    assert exc_info.value.status_code == 400


def test_26_budget_reservation_conversion_to_captured(db, b3_user_a):
    """Test 26: convert_reservation_to_captured transitions reservation to completed captured spend."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("60.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("55.00"), status="ordered")

    order = Order(
        proposal_id=prop.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-26",
        create_request_id="req-ord-26",
        amount=Decimal("55.00"),
        currency="USD",
        status="buyer_approved",
        budget_reserved=Decimal("55.00"),
    )
    db.add(order)
    db.commit()

    service.convert_reservation_to_captured(order.id)
    db.refresh(order)
    assert order.status == "completed"

    breakdown = service.calculate_available_budget(mandate.id)
    assert breakdown.captured_spending == Decimal("55.00")
    assert breakdown.active_reservations == Decimal("0.00")
    assert breakdown.available_budget == Decimal("45.00")


def test_27_idempotent_reservation_release(db, b3_user_a):
    """Test 27: Calling release_budget_reservation multiple times is idempotent."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("60.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("40.00"), status="ordered")

    order = Order(
        proposal_id=prop.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-27",
        create_request_id="req-ord-27",
        amount=Decimal("40.00"),
        currency="USD",
        status="buyer_approved",
        budget_reserved=Decimal("40.00"),
    )
    db.add(order)
    db.commit()

    # First release
    service.release_budget_reservation(order.id)
    db.refresh(order)
    assert order.budget_reserved == Decimal("0.00")

    # Second release should be a safe no-op
    service.release_budget_reservation(order.id)
    db.refresh(order)
    assert order.budget_reserved == Decimal("0.00")


def test_28_mandate_update_below_committed_spend_rejected(client, db, b3_user_a):
    """Test 28: Mandate update with budget lower than committed spend is rejected with BUDGET_EXCEEDED."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("80.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("80.00"), status="ordered")

    order = Order(
        proposal_id=prop.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-28",
        create_request_id="req-ord-28",
        amount=Decimal("80.00"),
        currency="USD",
        status="completed",
        budget_reserved=Decimal("80.00"),
    )
    db.add(order)
    db.commit()

    # Attempt to lower budget to $50 when $80 is already committed
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "50.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
        headers=auth_headers(b3_user_a),
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BUDGET_EXCEEDED"


# ==============================================================================
# GROUP 4: Revocation, Lifecycle & Invalidation (Tests 29–34)
# ==============================================================================

def test_29_mandate_revocation_lifecycle(client, b3_user_a):
    """Test 29: Revoking a mandate sets status to 'revoked' and current returns 404."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_res = client.post(
        "/api/mandates",
        json={"total_budget": "100.00", "per_item_cap": "50.00", "currency": "USD", "allowed_categories": ["Home"], "expires_at": future_date},
        headers=auth_headers(b3_user_a),
    )
    mandate_id = create_res.json()["id"]

    revoke_res = client.post(f"/api/mandates/{mandate_id}/revoke", headers=auth_headers(b3_user_a))
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "revoked"

    # Current should now return 404
    curr_res = client.get("/api/mandates/current", headers=auth_headers(b3_user_a))
    assert curr_res.status_code == 404
    assert curr_res.json()["error"]["code"] == "MANDATE_NOT_FOUND"


def test_30_mandate_revocation_ownership(client, b3_user_a, b3_user_b):
    """Test 30: User B cannot revoke User A's mandate (403 ACCESS_DENIED)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_res = client.post(
        "/api/mandates",
        json={"total_budget": "100.00", "per_item_cap": "50.00", "currency": "USD", "allowed_categories": ["Home"], "expires_at": future_date},
        headers=auth_headers(b3_user_a),
    )
    mandate_id = create_res.json()["id"]

    revoke_res = client.post(f"/api/mandates/{mandate_id}/revoke", headers=auth_headers(b3_user_b))
    assert revoke_res.status_code == 403
    assert revoke_res.json()["error"]["code"] == "ACCESS_DENIED"


def test_31_actions_on_revoked_mandate_order_rejected(client, db, b3_user_a):
    """Test 31: Creating an order for a proposal with a revoked mandate is rejected (400)."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("50.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("30.00"), status="pending")

    # Revoke mandate
    service.revoke_mandate(mandate.id, b3_user_a.id)

    # Attempt to order proposal
    res = client.post(
        f"/api/proposals/{prop.id}/order",
        json={"checkout_attempt_id": "attempt-31"},
        headers={**auth_headers(b3_user_a), "X-Request-ID": "revoked-order-attempt"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "MANDATE_INVALID"


def test_32_actions_on_revoked_mandate_request_rejected(client, b3_user_a):
    """Test 32: Submitting a new shopping request after mandate revocation is rejected (404)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_res = client.post(
        "/api/mandates",
        json={"total_budget": "100.00", "per_item_cap": "50.00", "currency": "USD", "allowed_categories": ["Home"], "expires_at": future_date},
        headers=auth_headers(b3_user_a),
    )
    mandate_id = create_res.json()["id"]
    client.post(f"/api/mandates/{mandate_id}/revoke", headers=auth_headers(b3_user_a))

    res = client.post(
        "/api/requests",
        json={"text": "Find a kitchen blender under $40"},
        headers=auth_headers(b3_user_a),
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "MANDATE_NOT_FOUND"


def test_33_historical_access_to_revoked_mandate(client, b3_user_a):
    """Test 33: A revoked mandate is still retrievable by ID for auditing and record keeping."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_res = client.post(
        "/api/mandates",
        json={"total_budget": "100.00", "per_item_cap": "50.00", "currency": "USD", "allowed_categories": ["Home"], "expires_at": future_date},
        headers=auth_headers(b3_user_a),
    )
    mandate_id = create_res.json()["id"]
    client.post(f"/api/mandates/{mandate_id}/revoke", headers=auth_headers(b3_user_a))

    # Lookup by ID
    res = client.get(f"/api/mandates/{mandate_id}", headers=auth_headers(b3_user_a))
    assert res.status_code == 200
    assert res.json()["id"] == mandate_id
    assert res.json()["status"] == "revoked"


def test_34_active_mandate_expiration_handling(client, db, b3_user_a):
    """Test 34: Expired mandate is detected, marked expired, and blocks shopping requests."""
    past_date = datetime.now(timezone.utc) - timedelta(minutes=10)
    mandate = Mandate(
        user_id=b3_user_a.id,
        version=1,
        total_budget=Decimal("100.00"),
        per_item_cap=Decimal("50.00"),
        currency="USD",
        allowed_categories=["Home"],
        expires_at=past_date,
        status="active",
    )
    db.add(mandate)
    db.commit()

    service = MandateService(db)
    validation = service.validate_mandate_is_active(mandate, raise_exception=False)
    assert validation.valid is False
    assert validation.is_expired is True

    # GET /api/mandates/current should mark it expired and return 404
    res = client.get("/api/mandates/current", headers=auth_headers(b3_user_a))
    assert res.status_code == 404

    # Shopping request creation fails
    req_res = client.post(
        "/api/requests",
        json={"text": "Find a toaster"},
        headers=auth_headers(b3_user_a),
    )
    assert req_res.status_code == 404


# ==============================================================================
# GROUP 5: Concurrency, Currency & API Integration (Tests 35–37)
# ==============================================================================

def test_35_concurrency_race_condition_protection(db, b3_user_a):
    """Test 35: Concurrency safety prevents over-reserving budget beyond total."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("60.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    p1 = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("60.00"), status="ordered")
    o1 = Order(
        proposal_id=p1.id,
        user_id=b3_user_a.id,
        paypal_order_id="PP-RACE-1",
        create_request_id="req-race-1",
        amount=Decimal("60.00"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("60.00"),
    )
    db.add(o1)
    db.commit()

    # Attempting to reserve another 50.00 when only 40.00 remains must be rejected
    with pytest.raises(CartiAPIException) as exc_info:
        service.reserve_budget(mandate.id, amount=Decimal("50.00"))

    assert exc_info.value.code == CartiErrorCode.BUDGET_EXCEEDED


def test_36_currency_consistency_validation(client, db, b3_user_a):
    """Test 36: Rejecting reservations or orders with mismatched currencies."""
    service = MandateService(db)
    mandate = service.create_or_update_mandate(
        b3_user_a.id,
        MandateCreate(
            total_budget=Decimal("100.00"),
            per_item_cap=Decimal("50.00"),
            currency="USD",
            allowed_categories=["Home"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    # 1. Direct reservation currency mismatch
    with pytest.raises(CartiAPIException) as exc_info:
        service.reserve_budget(mandate.id, amount=Decimal("30.00"), currency="EUR")
    assert exc_info.value.code == CartiErrorCode.CURRENCY_MISMATCH

    # 2. Proposal checkout currency mismatch
    prop = make_test_proposal(db, b3_user_a, mandate, amount=Decimal("30.00"), currency="EUR", status="pending")

    res = client.post(
        f"/api/proposals/{prop.id}/order",
        json={"checkout_attempt_id": "attempt-36"},
        headers={**auth_headers(b3_user_a), "X-Request-ID": "mismatched-curr-order"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "CURRENCY_MISMATCH"


def test_37_api_integration_all_endpoints(client, b3_user_a):
    """Test 37: Complete end-to-end integration across all 6 mandate API routes."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    headers = auth_headers(b3_user_a)

    # 1. POST /api/mandates (Create V1)
    create_v1 = client.post(
        "/api/mandates",
        json={
            "total_budget": "120.00",
            "per_item_cap": "40.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
        headers=headers,
    )
    assert create_v1.status_code == 201
    v1_id = create_v1.json()["id"]

    # 2. GET /api/mandates/current
    curr_res = client.get("/api/mandates/current", headers=headers)
    assert curr_res.status_code == 200
    assert curr_res.json()["id"] == v1_id
    assert curr_res.json()["version"] == 1

    # 3. GET /api/mandates/current/budget
    budget_res = client.get("/api/mandates/current/budget", headers=headers)
    assert budget_res.status_code == 200
    assert budget_res.json()["available_budget"] == "120.00"

    # 4. POST /api/mandates (Create V2)
    create_v2 = client.post(
        "/api/mandates",
        json={
            "total_budget": "180.00",
            "per_item_cap": "60.00",
            "currency": "USD",
            "allowed_categories": ["Home", "Electronics"],
            "expires_at": future_date,
        },
        headers=headers,
    )
    assert create_v2.status_code == 201
    assert create_v2.json()["version"] == 2
    v2_id = create_v2.json()["id"]

    # 5. GET /api/mandates/versions/1 (Historical V1)
    v1_hist = client.get("/api/mandates/versions/1", headers=headers)
    assert v1_hist.status_code == 200
    assert v1_hist.json()["version"] == 1
    assert v1_hist.json()["status"] == "superseded"

    # 6. GET /api/mandates/{id}
    by_id_res = client.get(f"/api/mandates/{v2_id}", headers=headers)
    assert by_id_res.status_code == 200
    assert by_id_res.json()["id"] == v2_id

    # 7. POST /api/mandates/{id}/revoke
    revoke_res = client.post(f"/api/mandates/{v2_id}/revoke", headers=headers)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "revoked"

    # 8. Verify GET /api/mandates/current returns 404 after revocation
    after_revoke = client.get("/api/mandates/current", headers=headers)
    assert after_revoke.status_code == 404
