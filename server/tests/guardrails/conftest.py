"""
Pytest fixtures and factories for Module B8 tests.

All fixtures are self-contained and isolated — they do NOT share or modify
any state from other modules' tests.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest

from server.app.services.ranking.models import MandateSnapshot
from server.app.services.guardrails.models import ProposalEvaluationRequest


# ---------------------------------------------------------------------------
# Standard mandate fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_mandate() -> MandateSnapshot:
    """Active, unexpired mandate with standard financial and category constraints."""
    return MandateSnapshot(
        total_budget=Decimal("200.00"),
        per_item_cap=Decimal("80.00"),
        currency="USD",
        allowed_categories=["Home Lighting", "Office Furniture", "Electronics"],
        blocked_categories=["Weapons", "Hazardous", "Adult"],
        allowed_retailers=["target.com", "bestbuy.com", "amazon.com", "walmart.com"],
        max_quantity=5,
        price_tolerance=Decimal("2.00"),
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )


@pytest.fixture
def mandate_no_caps() -> MandateSnapshot:
    """Active mandate with no spending caps or category restrictions."""
    return MandateSnapshot(
        currency="USD",
        status="active",
    )


@pytest.fixture
def expired_mandate() -> MandateSnapshot:
    """Mandate whose expiration timestamp has already elapsed."""
    return MandateSnapshot(
        total_budget=Decimal("200.00"),
        per_item_cap=Decimal("80.00"),
        currency="USD",
        status="active",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )


@pytest.fixture
def revoked_mandate() -> MandateSnapshot:
    """Mandate in 'revoked' lifecycle state."""
    return MandateSnapshot(
        total_budget=Decimal("200.00"),
        currency="USD",
        status="revoked",
    )


@pytest.fixture
def superseded_mandate() -> MandateSnapshot:
    """Mandate in 'superseded' lifecycle state."""
    return MandateSnapshot(
        total_budget=Decimal("200.00"),
        currency="USD",
        status="superseded",
    )


# ---------------------------------------------------------------------------
# Standard proposal factories
# ---------------------------------------------------------------------------

def make_proposal(
    candidate_id: str = "prod_lamp_001:off_target_1",
    product_id: str = "prod_lamp_001",
    offer_key: str = "off_target_1",
    product_title: str = "Lumina LED Desk Lamp",
    category: Optional[str] = "Home Lighting",
    domain: str = "target.com",
    buy_url: str = "https://buy.trychannel3.com/target/lamp001",
    price_amount: Decimal = Decimal("34.99"),
    currency: str = "USD",
    availability: str = "InStock",
    condition: str = "new",
    quantity: int = 1,
    attributes: Optional[dict[str, Any]] = None,
    observed_at: Optional[datetime] = None,
    b7_ranking_score: Optional[float] = None,
) -> ProposalEvaluationRequest:
    """Factory for ProposalEvaluationRequest with sensible defaults."""
    return ProposalEvaluationRequest(
        candidate_id=candidate_id,
        product_id=product_id,
        offer_key=offer_key,
        product_title=product_title,
        category=category,
        domain=domain,
        buy_url=buy_url,
        price_amount=price_amount,
        currency=currency,
        availability=availability,
        condition=condition,
        quantity=quantity,
        attributes=attributes or {"type": "desk", "dimmable": "true"},
        observed_at=observed_at or datetime.now(timezone.utc),
        b7_ranking_score=b7_ranking_score,
    )


@pytest.fixture
def valid_proposal() -> ProposalEvaluationRequest:
    """Standard, fully policy-compliant proposal."""
    return make_proposal()
