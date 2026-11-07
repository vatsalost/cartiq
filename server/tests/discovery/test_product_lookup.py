"""Tests for URL lookup endpoint POST /v1/lookup."""

import asyncio
from decimal import Decimal
import json
from typing import Any
import httpx
import pytest
from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.exceptions import (
    Channel3NotFoundError,
    Channel3ValidationError,
    InvalidURLError,
)
from server.app.services.discovery.services.lookup_service import LookupService
from server.tests.discovery.conftest import make_mock_client


def test_successful_url_lookup(sample_lookup_response: dict[str, Any]):
    """Test successful resolution of a retailer URL to a canonical product."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/lookup"
        assert request.method == "POST"
        body = json.loads(request.content.decode("utf-8"))
        assert body["url"] == "https://www.amazon.com/dp/B08N5WRWNW"
        return httpx.Response(200, json=sample_lookup_response)

    client = make_mock_client(handler)
    service = LookupService(client)

    async def run():
        product = await service.lookup_url("https://www.amazon.com/dp/B08N5WRWNW")
        assert product.product_id == "prod_202"
        assert product.title == "Wireless Studio Headphones"
        assert len(product.offers) == 1
        assert product.offers[0].domain == "amazon.com"
        assert product.offers[0].price_amount == Decimal("149.99")

    asyncio.run(run())


def test_invalid_url_rejected_locally():
    """Test malformed and non-HTTP URLs are blocked locally before HTTP request."""
    client = make_mock_client(lambda r: httpx.Response(200))
    service = LookupService(client)

    async def run():
        # Non-http scheme
        with pytest.raises(InvalidURLError, match="Invalid URL scheme"):
            await service.lookup_url("ftp://files.example.com/item")

        # Empty URL
        with pytest.raises(InvalidURLError, match="non-empty string"):
            await service.lookup_url("")

        # Prohibited localhost SSRF
        with pytest.raises(InvalidURLError, match="prohibited"):
            await service.lookup_url("http://localhost:8080/product")

        # Prohibited private IP SSRF
        with pytest.raises(InvalidURLError, match="private/internal IP"):
            await service.lookup_url("http://192.168.1.1/product")

        # Prohibited AWS metadata endpoint
        with pytest.raises(InvalidURLError, match="private/internal IP"):
            await service.lookup_url("http://169.254.169.254/latest/meta-data")

    asyncio.run(run())


def test_product_lookup_not_found():
    """Test 404 response raises Channel3NotFoundError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Product URL not in catalog"})

    client = make_mock_client(handler)
    service = LookupService(client)

    async def run():
        with pytest.raises(Channel3NotFoundError):
            await service.lookup_url("https://www.unknown-store.com/item/123")

    asyncio.run(run())


def test_lookup_empty_response_raises_not_found():
    """Test empty JSON object response from lookup translates to Channel3NotFoundError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_mock_client(handler)
    service = LookupService(client)

    async def run():
        with pytest.raises(Channel3NotFoundError):
            await service.lookup_url("https://www.example.com/product/abc")

    asyncio.run(run())
