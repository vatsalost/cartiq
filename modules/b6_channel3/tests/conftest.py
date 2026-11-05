"""Pytest fixtures and mock factories for Module B6 tests."""

import json
from typing import Any, Callable, Dict, Optional
import httpx
import pytest
from modules.b6_channel3.client.channel3_client import Channel3Client
from modules.b6_channel3.client.http_client import Channel3HTTPClient
from modules.b6_channel3.config import Channel3Config
from modules.b6_channel3.models.locale import Channel3Locale


@pytest.fixture
def test_config() -> Channel3Config:
    """Fixture providing test configuration with dummy API key."""
    return Channel3Config(
        api_key="test_ch3_secret_api_key_12345",
        base_url="https://api.trychannel3.com",
        timeout_seconds=5.0,
        connect_timeout_seconds=2.0,
        max_retries=2,
        backoff_factor=0.01,  # Fast retries during tests
        default_limit=10,
    )


@pytest.fixture
def default_locale() -> Channel3Locale:
    """Default US English USD test locale."""
    return Channel3Locale(country="US", language="en", currency="USD")


@pytest.fixture
def sample_search_response() -> dict[str, Any]:
    """Sample raw payload returned by POST /v1/search."""
    return {
        "products": [
            {
                "id": "prod_101",
                "title": "Minimalist LED Desk Lamp",
                "brands": [{"id": "b1", "name": "Lumina"}],
                "category": {"slug": "lighting", "title": "Home Lighting"},
                "description": "Touch dimmable warm LED desk lamp.",
                "images": [
                    "https://cdn.example.com/lamp1.jpg",
                    "https://cdn.example.com/lamp2.jpg",
                ],
                "attributes": {
                    "materials": ["Aluminum", "Plastic"],
                    "wattage": "12W",
                },
                "variants": [
                    {
                        "id": "var_black",
                        "name": "Matte Black",
                        "options": {"Color": "Black"},
                        "sku": "LUM-101-BLK",
                    }
                ],
                "offers": [
                    {
                        "domain": "target.com",
                        "merchant_name": "Target",
                        "url": "https://buy.trychannel3.com/target/101",
                        "price": {
                            "price": 39.99,
                            "currency": "USD",
                            "compare_at_price": 49.99,
                        },
                        "availability": "InStock",
                        "condition": "new",
                    },
                    {
                        "domain": "bestbuy.com",
                        "merchant_name": "Best Buy",
                        "url": "https://buy.trychannel3.com/bestbuy/101",
                        "price": 44.95,
                        "currency": "USD",
                        "availability": "InStock",
                        "condition": "new",
                    },
                ],
            }
        ],
        "next_page_token": "page_2",
    }


@pytest.fixture
def sample_lookup_response() -> dict[str, Any]:
    """Sample raw payload returned by POST /v1/lookup."""
    return {
        "product": {
            "id": "prod_202",
            "title": "Wireless Studio Headphones",
            "brand": "AudioTech",
            "category": "Electronics",
            "description": "Active noise-canceling wireless headphones.",
            "images": [
                {"url": "https://cdn.example.com/headphones.jpg", "is_primary": True}
            ],
            "gender": "unisex",
            "offers": [
                {
                    "domain": "amazon.com",
                    "merchant_id": "m_amzn",
                    "merchant_name": "Amazon",
                    "url": "https://buy.trychannel3.com/amazon/202",
                    "price": {
                        "price": 149.99,
                        "currency": "USD",
                    },
                    "availability": "InStock",
                    "condition": "new",
                }
            ],
        }
    }


@pytest.fixture
def sample_product_detail_response() -> dict[str, Any]:
    """Sample raw payload returned by GET /v1/products/{product_id}."""
    return {
        "id": "prod_303",
        "title": "Ergonomic Task Chair",
        "brand": "Herman Miller",
        "category": "Office Furniture",
        "description": "Ergonomic mesh chair with adjustable lumbar support.",
        "image_url": "https://cdn.example.com/chair.jpg",
        "variants": [
            {
                "id": "var_standard",
                "name": "Standard Charcoal",
                "options": {"Color": "Charcoal", "Size": "Medium"},
            }
        ],
        "offers": [
            {
                "domain": "officedepot.com",
                "merchant_id": "m_od",
                "merchant_name": "Office Depot",
                "url": "https://buy.trychannel3.com/officedepot/303",
                "price": 289.00,
                "currency": "USD",
                "availability": "InStock",
                "condition": "new",
            },
            {
                "domain": "wayfair.com",
                "merchant_id": "m_wf",
                "merchant_name": "Wayfair",
                "url": "https://buy.trychannel3.com/wayfair/303",
                "price": 310.00,
                "currency": "USD",
                "availability": "OutOfStock",
                "condition": "new",
            },
        ],
    }


def make_mock_client(
    handler: Callable[[httpx.Request], httpx.Response],
    config: Optional[Channel3Config] = None,
) -> Channel3Client:
    """Helper to instantiate Channel3Client backed by an in-memory mock transport."""
    cfg = config or Channel3Config(
        api_key="test_ch3_secret_api_key_12345",
        timeout_seconds=5.0,
        connect_timeout_seconds=2.0,
        max_retries=1,
        backoff_factor=0.01,
    )
    transport = httpx.MockTransport(handler)
    http_client = Channel3HTTPClient(config=cfg, transport=transport)
    return Channel3Client(config=cfg, http_client=http_client)
