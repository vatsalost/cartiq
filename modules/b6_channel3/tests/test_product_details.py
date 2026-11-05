"""Tests for product detail endpoint GET /v1/products/{product_id}."""

import asyncio
from decimal import Decimal
from typing import Any
import httpx
import pytest
from modules.b6_channel3.client.channel3_client import Channel3Client
from modules.b6_channel3.exceptions import (
    Channel3NotFoundError,
    Channel3ValidationError,
)
from modules.b6_channel3.services.product_service import ProductService
from modules.b6_channel3.tests.conftest import make_mock_client


def test_successful_product_detail_retrieval(sample_product_detail_response: dict[str, Any]):
    """Test retrieving full canonical product details with multiple offers."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/products/prod_303"
        assert request.method == "GET"
        return httpx.Response(200, json=sample_product_detail_response)

    client = make_mock_client(handler)
    service = ProductService(client)

    async def run():
        product = await service.get_product_details("prod_303")
        assert product.product_id == "prod_303"
        assert product.title == "Ergonomic Task Chair"
        assert len(product.offers) == 2
        assert len(product.variants) == 1
        assert product.variants[0].options["Color"] == "Charcoal"

    asyncio.run(run())


def test_product_detail_with_variant_options():
    """Test variant query parameters are properly appended to GET request."""
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_params
        captured_params = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "id": "prod_404",
                "title": "Variant Item",
                "offers": [{"domain": "store.com", "url": "https://buy.com", "price": 10.0, "currency": "USD", "availability": "InStock"}]
            }
        )

    client = make_mock_client(handler)

    async def run():
        await client.get_product("prod_404", variant_options={"Color": "Navy", "Size": "Large"})

    asyncio.run(run())
    assert captured_params.get("option_Color") == "Navy"
    assert captured_params.get("option_Size") == "Large"


def test_product_with_no_offers():
    """Test product with empty offers list normalizes cleanly."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_505",
                "title": "Discontinued Item",
                "offers": []
            }
        )

    client = make_mock_client(handler)

    async def run():
        product = await client.get_product("prod_505")
        assert product.product_id == "prod_505"
        assert product.offers == []
        assert product.get_best_price_offer() is None

    asyncio.run(run())


def test_product_missing_optional_metadata():
    """Test normalization handles absence of brand, category, images, or description."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "prod_minimal",
                "title": "Bare Minimal Product",
                "offers": [
                    {"domain": "shop.com", "url": "https://shop.com/item", "price": 12.00, "currency": "USD", "availability": "InStock"}
                ]
            }
        )

    client = make_mock_client(handler)

    async def run():
        p = await client.get_product("prod_minimal")
        assert p.product_id == "prod_minimal"
        assert p.title == "Bare Minimal Product"
        assert p.brand is None
        assert p.category is None
        assert p.description is None
        assert p.images == []
        assert len(p.offers) == 1

    asyncio.run(run())


def test_invalid_product_id_rejected():
    """Test blank product ID raises Channel3ValidationError before sending request."""
    client = make_mock_client(lambda r: httpx.Response(200))

    async def run():
        with pytest.raises(Channel3ValidationError, match="Product ID cannot be blank"):
            await client.get_product("   ")

    asyncio.run(run())
