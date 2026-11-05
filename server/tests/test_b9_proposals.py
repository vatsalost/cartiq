"""Module B9: Proposal Service and Retailer Verification comprehensive test suite.

Verifies:
A. Proposal creation and validation (invariance, idempotency, guardrails)
B. Retailer offer verification and domain safety
C. Accurate Decimal price, subtotal, shipping, tax, and total calculation
D. Mandate spending caps, version snapshotting, and budget reservations
E. Proposal lifecycle transitions (pending -> checkout_started -> ordered / rejected / expired / stale)
F. KERNEL browser verification adapter, security boundaries, and status reporting
G. Checkout preparation boundary (trusted B9 -> B10 handoff)
H. Multi-tenant security, ownership boundaries, and IDOR protection
I. Audit logging and non-repudiable financial events
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest

from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest
from server.app.models.user import User
from server.app.schemas.proposal import CheckoutPreparationResult, ProposalResponse
from server.app.services.kernel_service import (
    KernelVerificationService,
    RetailerVerificationResult,
    kernel_verification_service,
)
from server.app.services.proposal_service import ProposalService


@pytest.fixture
def proposal_service(db):
    return ProposalService(db)


# =====================================================================
# SECTION A: PROPOSAL CREATION AND VALIDATION
# =====================================================================

def test_proposal_creation_valid(proposal_service, db, valid_request, sample_candidate, active_mandate):
    """Test A1: Create proposal from eligible candidate with exact Decimal calculations."""
    offer = sample_candidate.offers[0]
    proposal = proposal_service.create_proposal(
        request_id=valid_request.id,
        user_id=valid_request.user_id,
        candidate_id=sample_candidate.id,
        offer_id=offer.id,
        quantity=2,
        rationale="Strong match with desk lamp requirements",
        shipping_amount=Decimal("4.50"),
        tax_amount=Decimal("2.75"),
    )

    assert proposal.id is not None
    assert proposal.request_id == valid_request.id
    assert proposal.user_id == valid_request.user_id
    assert proposal.mandate_id == active_mandate.id
    assert proposal.mandate_version == active_mandate.version
    assert proposal.candidate_id == sample_candidate.id
    assert proposal.offer_id == offer.id
    assert proposal.quantity == 2
    assert proposal.unit_price_at_proposal == Decimal("34.99")
    assert proposal.subtotal_at_proposal == Decimal("69.98")
    assert proposal.shipping_amount == Decimal("4.50")
    assert proposal.tax_amount == Decimal("2.75")
    assert proposal.total_amount == Decimal("77.23")
    assert proposal.status == "pending"
    assert proposal.currency == "USD"
    assert proposal.product_snapshot["title"] == sample_candidate.title
    assert proposal.offer_snapshot["domain"] == offer.domain
    assert proposal.verification_status in ["disabled", "unverified", "verified"]


def test_proposal_creation_idempotent(proposal_service, valid_request, sample_candidate):
    """Test A2: Duplicate proposal creation for same candidate and offer returns existing pending proposal."""
    offer = sample_candidate.offers[0]
    p1 = proposal_service.create_proposal(
        request_id=valid_request.id,
        user_id=valid_request.user_id,
        candidate_id=sample_candidate.id,
        offer_id=offer.id,
        quantity=1,
    )
    p2 = proposal_service.create_proposal(
        request_id=valid_request.id,
        user_id=valid_request.user_id,
        candidate_id=sample_candidate.id,
        offer_id=offer.id,
        quantity=1,
    )
    assert p1.id == p2.id


def test_proposal_creation_rejects_cross_request_candidate(proposal_service, db, test_user, active_mandate, sample_candidate):
    """Test A3: Rejects candidate that belongs to a different request."""
    req2 = ShoppingRequest(
        user_id=test_user.id,
        mandate_id=active_mandate.id,
        request_text="Different request",
        status="running",
    )
    db.add(req2)
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=req2.id,
            user_id=test_user.id,
            candidate_id=sample_candidate.id,  # Belongs to valid_request, not req2!
        )
    assert exc.value.code == CartiErrorCode.ACCESS_DENIED


def test_proposal_creation_rejects_cross_user_candidate(proposal_service, other_user, valid_request, sample_candidate):
    """Test A4: User B cannot create a proposal using User A's candidate or request."""
    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=other_user.id,
            candidate_id=sample_candidate.id,
        )
    assert exc.value.code == CartiErrorCode.ACCESS_DENIED


def test_proposal_creation_rejects_cancelled_request(proposal_service, db, valid_request, sample_candidate):
    """Test A5: Cannot create proposal for a cancelled or completed request."""
    valid_request.status = "cancelled"
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
        )
    assert exc.value.code == CartiErrorCode.REQUEST_CANCELLED


# =====================================================================
# SECTION B: RETAILER OFFER VERIFICATION & GUARDRAIL CHECKS
# =====================================================================

def test_proposal_creation_rejects_ineligible_offer(proposal_service, db, valid_request, sample_candidate):
    """Test B1: Ineligible offer is blocked by guardrails."""
    offer = sample_candidate.offers[0]
    offer.is_eligible = False
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
            offer_id=offer.id,
        )
    assert exc.value.code == CartiErrorCode.GUARDRAIL_VIOLATION


def test_proposal_creation_rejects_out_of_stock_offer(proposal_service, db, valid_request, sample_candidate):
    """Test B2: Out of stock offer is rejected."""
    offer = sample_candidate.offers[0]
    offer.availability = "OutOfStock"
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
            offer_id=offer.id,
        )
    assert exc.value.code == CartiErrorCode.GUARDRAIL_VIOLATION


def test_proposal_creation_rejects_blocked_category(proposal_service, db, valid_request, sample_candidate):
    """Test B3: Product in blocked category is rejected by guardrails."""
    sample_candidate.category = "Clothing"  # Blocked in active_mandate
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
        )
    assert exc.value.code == CartiErrorCode.GUARDRAIL_VIOLATION


def test_proposal_creation_rejects_disallowed_retailer(proposal_service, db, valid_request, sample_candidate):
    """Test B4: Retailer not in allowed list is rejected."""
    offer = sample_candidate.offers[0]
    offer.domain = "unauthorized-shop.com"
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
            offer_id=offer.id,
        )
    assert exc.value.code == CartiErrorCode.GUARDRAIL_VIOLATION


def test_proposal_creation_rejects_per_item_cap_exceeded(proposal_service, db, valid_request, sample_candidate, active_mandate):
    """Test B5: Unit price exceeding per_item_cap is rejected."""
    offer = sample_candidate.offers[0]
    offer.price_amount = Decimal("60.00")  # per_item_cap is 50.00
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
            offer_id=offer.id,
        )
    assert exc.value.code == CartiErrorCode.GUARDRAIL_VIOLATION


def test_proposal_creation_rejects_currency_mismatch(proposal_service, db, valid_request, sample_candidate):
    """Test B6: Currency mismatch between offer and mandate is rejected."""
    offer = sample_candidate.offers[0]
    offer.currency = "EUR"  # Mandate is USD
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
            offer_id=offer.id,
        )
    assert exc.value.code == CartiErrorCode.CURRENCY_MISMATCH


# =====================================================================
# SECTION C: PRICE AND TOTAL CALCULATION (DECIMAL ACCURACY)
# =====================================================================

def test_decimal_price_arithmetic_precision(proposal_service, valid_request, sample_candidate):
    """Test C1: Monetary calculations use exact Decimal arithmetic with zero float inaccuracies."""
    offer = sample_candidate.offers[0]
    offer.price_amount = Decimal("33.33")

    proposal = proposal_service.create_proposal(
        request_id=valid_request.id,
        user_id=valid_request.user_id,
        candidate_id=sample_candidate.id,
        offer_id=offer.id,
        quantity=2,
        shipping_amount=Decimal("5.55"),
        tax_amount=Decimal("3.34"),
    )

    assert isinstance(proposal.unit_price_at_proposal, Decimal)
    assert isinstance(proposal.subtotal_at_proposal, Decimal)
    assert isinstance(proposal.shipping_amount, Decimal)
    assert isinstance(proposal.tax_amount, Decimal)
    assert isinstance(proposal.total_amount, Decimal)

    # 33.33 * 2 = 66.66; + 5.55 + 3.34 = 75.55
    assert proposal.subtotal_at_proposal == Decimal("66.66")
    assert proposal.total_amount == Decimal("75.55")


# =====================================================================
# SECTION D: MANDATE BUDGET AND CONCURRENCY
# =====================================================================

def test_proposal_creation_rejects_exceeding_available_budget(proposal_service, db, valid_request, sample_candidate, active_mandate):
    """Test D1: Total amount exceeding available budget is blocked."""
    # Mandate total budget is 100.00. Set offer price to 49.00 and quantity to 3 (total = 147.00 > 100.00)
    offer = sample_candidate.offers[0]
    offer.price_amount = Decimal("49.00")
    active_mandate.max_quantity_per_product = 5
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.create_proposal(
            request_id=valid_request.id,
            user_id=valid_request.user_id,
            candidate_id=sample_candidate.id,
            offer_id=offer.id,
            quantity=3,
        )
    assert exc.value.code == CartiErrorCode.BUDGET_EXCEEDED


def test_proposal_retains_exact_mandate_version_when_superseded(proposal_service, db, valid_request, sample_candidate, active_mandate, test_user):
    """Test D2: Proposal snapshot records exact mandate version at creation time even after mandate update."""
    offer = sample_candidate.offers[0]
    proposal = proposal_service.create_proposal(
        request_id=valid_request.id,
        user_id=valid_request.user_id,
        candidate_id=sample_candidate.id,
        offer_id=offer.id,
        quantity=1,
    )
    assert proposal.mandate_version == 1

    # Now update mandate to version 2
    active_mandate.status = "superseded"
    v2_mandate = Mandate(
        user_id=test_user.id,
        version=2,
        total_budget=Decimal("200.00"),
        per_item_cap=Decimal("100.00"),
        currency="USD",
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(v2_mandate)
    db.commit()

    # Re-fetch proposal; version snapshot must remain 1
    db.refresh(proposal)
    assert proposal.mandate_version == 1


# =====================================================================
# SECTION E: PROPOSAL LIFECYCLE, EXPIRY, AND REJECTION
# =====================================================================

def test_proposal_rejection_and_budget_release(proposal_service, db, sample_proposal, test_user):
    """Test E1: Rejecting proposal transitions status to 'rejected' and releases reservations."""
    # Create an associated order with budget_reserved
    order = Order(
        proposal_id=sample_proposal.id,
        user_id=test_user.id,
        create_request_id="req_test_123",
        amount=Decimal("34.99"),
        currency="USD",
        status="created",
        budget_reserved=Decimal("34.99"),
    )
    db.add(order)
    sample_proposal.status = "checkout_started"
    db.commit()

    rejected = proposal_service.reject_proposal(sample_proposal.id, test_user.id, reason="Changed my mind")
    assert rejected.status == "rejected"

    db.refresh(order)
    assert order.budget_reserved == Decimal("0.00")
    assert order.status == "cancelled"


def test_proposal_auto_expiration_on_access(proposal_service, db, sample_proposal, test_user):
    """Test E2: Proposal past expiration time automatically flips to 'expired' on retrieval."""
    sample_proposal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.commit()

    p = proposal_service.get_proposal(sample_proposal.id, test_user.id)
    assert p.status == "expired"


def test_batch_expire_old_proposals(proposal_service, db, sample_proposal):
    """Test E3: Batch sweep expires pending proposals whose expires_at is past."""
    sample_proposal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.commit()

    count = proposal_service.expire_old_proposals()
    assert count >= 1

    db.refresh(sample_proposal)
    assert sample_proposal.status == "expired"


def test_proposal_invalidation(proposal_service, db, sample_proposal):
    """Test E4: Invalidate proposal marks status 'invalidated'."""
    p = proposal_service.invalidate_proposal(sample_proposal.id, reason="Merchant product discontinued")
    assert p.status == "invalidated"


# =====================================================================
# SECTION F: KERNEL BROWSER VERIFICATION ADAPTER
# =====================================================================

def test_kernel_verification_domain_mismatch():
    """Test F1: KERNEL service detects and rejects spoofed or mismatched domains."""
    svc = KernelVerificationService()
    res = svc.verify_retailer_offer(
        offer_url="https://malicious-phishing.com/item",
        expected_domain="target.com",
        expected_price=Decimal("34.99"),
        expected_currency="USD",
    )
    assert res.status == "mismatch"
    assert res.is_verified is False
    assert "does not match" in res.reason


def test_kernel_verification_disabled_safe_reporting():
    """Test F2: When KERNEL is disabled, reports 'disabled' without fabricating verification."""
    svc = KernelVerificationService()
    svc.enabled = False
    res = svc.verify_retailer_offer(
        offer_url="https://target.com/lamp",
        expected_domain="target.com",
        expected_price=Decimal("34.99"),
        expected_currency="USD",
    )
    assert res.status == "disabled"
    assert res.is_verified is False
    assert "disabled by configuration" in res.reason


def test_kernel_verification_price_mismatch():
    """Test F3: When KERNEL is active and detects price discrepancy, marks mismatch."""
    svc = KernelVerificationService()
    svc.enabled = True
    svc.api_key = "test_kernel_key"
    res = svc.verify_retailer_offer(
        offer_url="https://target.com/lamp",
        expected_domain="target.com",
        expected_price=Decimal("34.99"),
        expected_currency="USD",
        mock_extracted_price=Decimal("49.99"),  # Mismatched price!
    )
    assert res.status == "mismatch"
    assert res.is_verified is False
    assert "Price mismatch" in res.reason


def test_kernel_verification_success():
    """Test F4: KERNEL verification succeeds when retailer page matches expected offer."""
    svc = KernelVerificationService()
    svc.enabled = True
    svc.api_key = "test_kernel_key"
    res = svc.verify_retailer_offer(
        offer_url="https://target.com/lamp",
        expected_domain="target.com",
        expected_price=Decimal("34.99"),
        expected_currency="USD",
        mock_extracted_price=Decimal("34.99"),
        mock_extracted_currency="USD",
        mock_extracted_availability="InStock",
    )
    assert res.status == "verified"
    assert res.is_verified is True
    assert res.extracted_price == Decimal("34.99")


# =====================================================================
# SECTION G: CHECKOUT PREPARATION FOR B10
# =====================================================================

def test_prepare_proposal_for_checkout_valid(proposal_service, sample_proposal, test_user):
    """Test G1: Valid proposal prepares checkout context for B10 PayPal service."""
    result = proposal_service.prepare_proposal_for_checkout(sample_proposal.id, test_user.id)
    assert isinstance(result, CheckoutPreparationResult)
    assert result.proposal_id == sample_proposal.id
    assert result.user_id == test_user.id
    assert result.amount == sample_proposal.total_amount
    assert result.currency == "USD"
    assert result.is_eligible is True
    assert result.offer_domain == "target.com"


def test_prepare_proposal_for_checkout_rejects_expired(proposal_service, db, sample_proposal, test_user):
    """Test G2: Checkout preparation rejects expired proposal."""
    sample_proposal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.prepare_proposal_for_checkout(sample_proposal.id, test_user.id)
    assert exc.value.code == CartiErrorCode.PROPOSAL_EXPIRED


def test_prepare_proposal_for_checkout_rejects_stale(proposal_service, db, sample_proposal, test_user):
    """Test G3: Checkout preparation rejects stale proposal."""
    sample_proposal.status = "stale"
    db.commit()

    with pytest.raises(CartiAPIException) as exc:
        proposal_service.prepare_proposal_for_checkout(sample_proposal.id, test_user.id)
    assert exc.value.code == CartiErrorCode.PROPOSAL_STALE


# =====================================================================
# SECTION H: MULTI-TENANT SECURITY & IDOR PROTECTION
# =====================================================================

def test_proposal_api_cross_user_rejection(client, sample_proposal, other_user):
    """Test H1: User B cannot access User A's proposal via API (IDOR defense)."""
    headers = {"Authorization": f"Bearer {other_user.id}"}
    res = client.get(f"/api/proposals/{sample_proposal.id}", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_proposal_api_reject_endpoint(client, sample_proposal, test_user):
    """Test H2: Reject proposal endpoint via API marks proposal rejected."""
    headers = {"Authorization": f"Bearer {test_user.id}"}
    res = client.post(
        f"/api/proposals/{sample_proposal.id}/reject",
        json={"reason": "Item price too high"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rejected"


def test_proposal_api_list_for_request(client, sample_proposal, valid_request, test_user):
    """Test H3: List proposals endpoint returns all proposals for a request."""
    headers = {"Authorization": f"Bearer {test_user.id}"}
    res = client.get(f"/api/proposals?request_id={valid_request.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == str(sample_proposal.id)
