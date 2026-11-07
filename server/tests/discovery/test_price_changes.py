"""Tests for pre-checkout offer freshness and price change detection."""

import asyncio
from decimal import Decimal
from typing import Any
import httpx
import pytest
from server.app.services.discovery.constants import OfferAvailability, RefreshStatus
from server.app.services.discovery.models.offer import NormalizedOffer
from server.app.services.discovery.normalizers.offer_normalizer import OfferNormalizer
from server.app.services.discovery.services.product_service import ProductService
from server.tests.discovery.conftest import make_mock_client


@pytest.fixture
def baseline_raw() -> dict[str, Any]:
    return {
        "id": "fixed_123",
        "domain": "bestbuy.com",
        "url": "https://buy.trychannel3.com/bestbuy/item",
        "price": 100.00,
        "currency": "USD",
        "availability": "InStock",
        "condition": "new",
    }


@pytest.fixture
def baseline_offer(baseline_raw: dict[str, Any]) -> NormalizedOffer:
    return OfferNormalizer.normalize_offer(baseline_raw)


def test_freshness_price_unchanged(baseline_offer: NormalizedOffer):
    """Test offer remains identical upon refresh."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_x",
                "title": "Item X",
                "offers": [
                    {
                        "id": "fixed_123",
                        "domain": "bestbuy.com",
                        "url": "https://buy.trychannel3.com/bestbuy/item",
                        "price": 100.00,
                        "currency": "USD",
                        "availability": "InStock",
                    }
                ],
            },
        )

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        res = await service.refresh_product("prod_x", baseline_offer.offer_key, baseline_offer=baseline_offer)
        assert res.status == RefreshStatus.UNCHANGED
        assert res.is_safe_for_checkout is True
        assert res.new_price == Decimal("100.00")

    asyncio.run(run())


def test_freshness_price_increased(baseline_offer: NormalizedOffer):
    """Test price hike is detected and flags checkout."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_x",
                "title": "Item X",
                "offers": [
                    {
                        "id": "fixed_123",
                        "domain": "bestbuy.com",
                        "url": "https://buy.trychannel3.com/bestbuy/item",
                        "price": 115.00,
                        "currency": "USD",
                        "availability": "InStock",
                    }
                ],
            },
        )

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        res = await service.refresh_product("prod_x", baseline_offer.offer_key, baseline_offer=baseline_offer)
        assert res.status == RefreshStatus.PRICE_CHANGED
        assert res.is_safe_for_checkout is False
        assert res.old_price == Decimal("100.00")
        assert res.new_price == Decimal("115.00")

    asyncio.run(run())


def test_freshness_price_decreased(baseline_offer: NormalizedOffer):
    """Test price reduction is detected."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_x",
                "title": "Item X",
                "offers": [
                    {
                        "id": "fixed_123",
                        "domain": "bestbuy.com",
                        "url": "https://buy.trychannel3.com/bestbuy/item",
                        "price": 85.00,
                        "currency": "USD",
                        "availability": "InStock",
                    }
                ],
            },
        )

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        res = await service.refresh_product("prod_x", baseline_offer.offer_key, baseline_offer=baseline_offer)
        assert res.status == RefreshStatus.PRICE_CHANGED
        assert res.new_price == Decimal("85.00")

    asyncio.run(run())


def test_freshness_currency_changed(baseline_offer: NormalizedOffer):
    """Test currency shift is detected."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_x",
                "title": "Item X",
                "offers": [
                    {
                        "id": "fixed_123",
                        "domain": "bestbuy.com",
                        "url": "https://buy.trychannel3.com/bestbuy/item",
                        "price": 100.00,
                        "currency": "EUR",  # Switched to EUR
                        "availability": "InStock",
                    }
                ],
            },
        )

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        res = await service.refresh_product("prod_x", baseline_offer.offer_key, baseline_offer=baseline_offer)
        assert res.status == RefreshStatus.CURRENCY_CHANGED
        assert res.is_safe_for_checkout is False

    asyncio.run(run())


def test_freshness_offer_disappeared(baseline_offer: NormalizedOffer):
    """Test offer missing from refreshed product returns OFFER_DISAPPEARED."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_x",
                "title": "Item X",
                "offers": [],  # Offer dropped off
            },
        )

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        res = await service.refresh_product("prod_x", baseline_offer.offer_key, baseline_offer=baseline_offer)
        assert res.status == RefreshStatus.OFFER_DISAPPEARED
        assert res.selected_offer is None
        assert res.is_safe_for_checkout is False

    asyncio.run(run())


def test_freshness_availability_changed(baseline_offer: NormalizedOffer):
    """Test stock depletion (InStock -> OutOfStock) is detected."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_x",
                "title": "Item X",
                "offers": [
                    {
                        "id": "fixed_123",
                        "domain": "bestbuy.com",
                        "url": "https://buy.trychannel3.com/bestbuy/item",
                        "price": 100.00,
                        "currency": "USD",
                        "availability": "OutOfStock",  # Became OOS
                    }
                ],
            },
        )

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        res = await service.refresh_product("prod_x", baseline_offer.offer_key, baseline_offer=baseline_offer)
        assert res.status == RefreshStatus.AVAILABILITY_CHANGED
        assert res.new_availability == OfferAvailability.OUT_OF_STOCK.value
        assert res.is_safe_for_checkout is False

    asyncio.run(run())
