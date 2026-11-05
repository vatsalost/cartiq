"""Pytest fixtures and test factories for Module B7 tests."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
import pytest
from server.app.services.ranking.config import RankingConfig, ScoringWeights
from server.app.services.ranking.interfaces import ILLMExplanationAdapter
from server.app.services.ranking.models import (
    CandidateOffer,
    CandidateOption,
    CandidateProduct,
    MandateSnapshot,
    ShoppingRequest,
)


@pytest.fixture
def default_request() -> ShoppingRequest:
    """Standard user shopping request."""
    return ShoppingRequest(
        original_text="Need a dimmable LED desk lamp under $45",
        category="Home Lighting",
        required_attributes={"type": "desk", "dimmable": "true"},
        preferred_attributes={"color": "black", "usb_port": "true"},
        max_price=Decimal("45.00"),
        currency="USD",
        preferred_brands=["Lumina"],
        preferred_retailers=["target.com", "bestbuy.com"],
        required_condition="new",
    )


@pytest.fixture
def default_mandate() -> MandateSnapshot:
    """Standard spending mandate snapshot."""
    return MandateSnapshot(
        total_budget=Decimal("100.00"),
        per_item_cap=Decimal("50.00"),
        currency="USD",
        allowed_categories=["Home Lighting", "Office Furniture", "Electronics"],
        blocked_categories=["Weapons", "Hazardous", "Adult"],
        allowed_retailers=["target.com", "bestbuy.com", "amazon.com", "walmart.com"],
        status="active",
    )


@pytest.fixture
def default_config() -> RankingConfig:
    """Standard ranking configuration with 24h freshness."""
    return RankingConfig(
        weights=ScoringWeights(
            price_weight=0.35,
            preferred_attributes_weight=0.25,
            preferred_brands_weight=0.15,
            preferred_retailers_weight=0.15,
            condition_weight=0.05,
            data_quality_weight=0.05,
        ),
        max_data_age_seconds=86400,
    )


def make_candidate_option(
    product_id: str = "prod_1",
    title: str = "Lumina Touch Desk Lamp",
    brand: Optional[str] = "Lumina",
    category: str = "Home Lighting",
    description: str = "High quality dimmable LED lamp with touch controls.",
    attributes: Optional[dict[str, Any]] = None,
    image_url: Optional[str] = "https://cdn.example.com/lamp.jpg",
    offer_key: str = "off_target_1",
    domain: str = "target.com",
    price: Decimal = Decimal("34.99"),
    currency: str = "USD",
    availability: str = "InStock",
    condition: str = "new",
    buy_url: str = "https://buy.trychannel3.com/target/1",
    observed_at: Optional[datetime] = None,
) -> CandidateOption:
    """Helper factory to instantiate CandidateOption instances for tests."""
    attrs = attributes if attributes is not None else {"type": "desk", "dimmable": "true", "color": "black"}
    ts = observed_at or datetime.now(timezone.utc)

    prod = CandidateProduct(
        product_id=product_id,
        title=title,
        brand=brand,
        category=category,
        description=description,
        attributes=attrs,
        image_url=image_url,
        observed_at=ts,
    )

    off = CandidateOffer(
        offer_key=offer_key,
        domain=domain,
        buy_url=buy_url,
        price_amount=price,
        currency=currency,
        availability=availability,
        condition=condition,
        observed_at=ts,
    )

    return CandidateOption.create(product=prod, offer=off)


class MockLLMAdapter(ILLMExplanationAdapter):
    """Mock LLM adapter for testing explanation drafting and error handling."""

    def __init__(self, should_fail: bool = False, return_text: Optional[str] = None):
        self.should_fail = should_fail
        self.return_text = return_text

    async def draft_explanation(self, facts: dict[str, object]) -> Optional[str]:
        if self.should_fail:
            raise RuntimeError("LLM service unavailable")
        return self.return_text
