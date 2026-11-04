"""Pytest fixtures and test environment setup."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test environment
os.environ["APP_ENV"] = "test"
os.environ["DEMO_USER_ENABLED"] = "true"

from server.app.core.security import AuthenticatedUser
from server.app.db.session import Base, get_db
from server.app.main import app
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest
from server.app.models.user import User

from sqlalchemy import event

# In-memory SQLite for fast isolated tests
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key enforcement in tests."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from server.app.services.agent_orchestrator import agent_orchestrator
agent_orchestrator.session_factory = TestingSessionLocal


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure a fresh database schema for every test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(clean_db):
    """Provide clean database session per test, cleanly closed after test."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db):
    """Provide TestClient with get_db overridden to use test session."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db) -> AuthenticatedUser:
    """Create default test user in database."""
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id, email="demo-user@carti.local")
        db.add(user)
        db.commit()
    return AuthenticatedUser(id=user.id, email=user.email, is_demo=True)


@pytest.fixture
def other_user(db) -> AuthenticatedUser:
    """Create secondary user for ownership boundary tests."""
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id, email="other-user@carti.local")
        db.add(user)
        db.commit()
    return AuthenticatedUser(id=user.id, email=user.email, is_demo=False)


@pytest.fixture
def active_mandate(db, test_user) -> Mandate:
    """Create a valid active mandate for test user."""
    mandate = Mandate(
        user_id=test_user.id,
        version=1,
        total_budget=Decimal("100.00"),
        per_item_cap=Decimal("50.00"),
        currency="USD",
        allowed_categories=["Home", "Electronics"],
        blocked_categories=["Clothing"],
        allowed_retailers=["target.com", "amazon.com"],
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
def valid_request(db, test_user, active_mandate) -> ShoppingRequest:
    """Create a sample shopping request."""
    req = ShoppingRequest(
        user_id=test_user.id,
        mandate_id=active_mandate.id,
        request_text="Find a warm-light desk lamp under $40",
        normalized_intent={"category": "Home", "max_price": "40.00"},
        status="running",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def sample_candidate(db, valid_request) -> Candidate:
    """Create a sample candidate with retailer offers."""
    candidate = Candidate(
        request_id=valid_request.id,
        provider_product_id="prod_c3_123",
        title="Modern Adjustable Desk Lamp",
        brand="Lumina",
        category="Home",
        image_url="https://example.com/lamp.jpg",
        attributes={"light_type": "warm", "adjustable": True},
        rank_score=Decimal("0.9500"),
        rank_reason="Best match for budget and warm light requirement.",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    offer = CandidateOffer(
        candidate_id=candidate.id,
        provider_offer_id="off_target_1",
        domain="target.com",
        buy_url="https://target.com/lamp",
        price_amount=Decimal("34.99"),
        currency="USD",
        availability="InStock",
        condition="new",
        is_eligible=True,
    )
    db.add(offer)
    db.commit()
    db.refresh(candidate)
    return candidate


@pytest.fixture
def sample_proposal(db, test_user, active_mandate, valid_request, sample_candidate) -> Proposal:
    """Create a proposal snapshot."""
    offer = sample_candidate.offers[0]
    proposal = Proposal(
        request_id=valid_request.id,
        user_id=test_user.id,
        mandate_id=active_mandate.id,
        candidate_id=sample_candidate.id,
        offer_id=offer.id,
        quantity=1,
        unit_price_at_proposal=offer.price_amount,
        subtotal_at_proposal=offer.price_amount,
        currency="USD",
        rationale="Matches warm-light specification and is within $50 cap.",
        guardrail_result={"passed": True, "checks": []},
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal
