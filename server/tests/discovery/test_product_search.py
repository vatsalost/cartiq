"""Tests for product search endpoint POST /v1/search."""

import asyncio
from decimal import Decimal
import json
from typing import Any
import httpx
import pytest
from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.exceptions import (
    Channel3AuthError,
    Channel3RateLimitError,
    Channel3TimeoutError,
    Channel3ValidationError,
)
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.services.search_service import SearchService
from server.tests.discovery.conftest import make_mock_client


def test_successful_product_search(sample_search_response: dict[str, Any], default_locale: Channel3Locale):
    """Test successful parsing and normalization of search results."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/search"
        assert request.method == "POST"
        body = json.loads(request.content.decode("utf-8"))
        assert body["query"] == "desk lamp"
        assert body["limit"] == 10
        return httpx.Response(200, json=sample_search_response)

    client = make_mock_client(handler)
    service = SearchService(client)

    async def run():
        results = await service.search(query="desk lamp", limit=10, locale=default_locale)
        assert len(results) == 1
        product = results[0]
        assert product.product_id == "prod_101"
        assert product.title == "Minimalist LED Desk Lamp"
        assert product.brand == "Lumina"
        assert len(product.offers) == 2
        assert product.offers[0].domain == "target.com"
        assert product.offers[0].price_amount == Decimal("39.99")
        assert product.offers[0].currency == "USD"
        assert product.offers[1].domain == "bestbuy.com"
        assert product.offers[1].price_amount == Decimal("44.95")

    asyncio.run(run())


def test_empty_search_results():
    """Test empty search array handling."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"products": []})

    client = make_mock_client(handler)

    async def run():
        results = await client.search_products(query="nonexistent item")
        assert results == []

    asyncio.run(run())


def test_multiple_returned_products():
    """Test response containing multiple products."""
    multi_payload = {
        "products": [
            {
                "id": "item_1",
                "title": "Item 1",
                "offers": [{"domain": "store1.com", "url": "https://buy.com/1", "price": 10.0, "currency": "USD", "availability": "InStock"}]
            },
            {
                "id": "item_2",
                "title": "Item 2",
                "offers": [{"domain": "store2.com", "url": "https://buy.com/2", "price": 20.0, "currency": "USD", "availability": "InStock"}]
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=multi_payload)

    client = make_mock_client(handler)

    async def run():
        results = await client.search_products(query="gadgets")
        assert len(results) == 2
        assert results[0].product_id == "item_1"
        assert results[1].product_id == "item_2"

    asyncio.run(run())


def test_empty_query_raises_validation_error():
    """Test empty or whitespace-only search query is rejected prior to network request."""
    client = make_mock_client(lambda r: httpx.Response(200))

    async def run():
        with pytest.raises(Channel3ValidationError, match="Search query cannot be empty"):
            await client.search_products(query="   ")

    asyncio.run(run())


def test_search_authentication_failure():
    """Test 401 response raises Channel3AuthError without retries."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid API Key"})

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3AuthError):
            await client.search_products(query="laptop")

    asyncio.run(run())


def test_search_rate_limiting_exhausted():
    """Test 429 response retries and raises Channel3RateLimitError."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(429, headers={"Retry-After": "0.01"}, json={"error": "Rate limit exceeded"})

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3RateLimitError):
            await client.search_products(query="phone")

    asyncio.run(run())
    assert call_count > 1


def test_search_provider_timeout():
    """Test request timeout translates to Channel3TimeoutError."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout reading from socket")

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3TimeoutError):
            await client.search_products(query="tablet")

    asyncio.run(run())
