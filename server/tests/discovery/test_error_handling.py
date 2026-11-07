"""Tests for Channel3 API error scenarios, retries, and network faults."""

import asyncio
import httpx
import pytest
from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.config import Channel3Config
from server.app.services.discovery.exceptions import (
    Channel3AuthError,
    Channel3BadRequestError,
    Channel3NetworkError,
    Channel3NotFoundError,
    Channel3RateLimitError,
    Channel3ServerError,
    Channel3TimeoutError,
)
from server.tests.discovery.conftest import make_mock_client


def test_error_400_bad_request():
    """Test 400 Bad Request raises Channel3BadRequestError with server message."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "Malformed filter syntax"})

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3BadRequestError, match="Malformed filter syntax"):
            await client.search_products(query="shoes")

    asyncio.run(run())


def test_error_403_forbidden():
    """Test 403 Forbidden raises Channel3AuthError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "Access denied"})

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3AuthError):
            await client.get_product("prod_1")

    asyncio.run(run())


def test_error_404_not_found():
    """Test 404 raises Channel3NotFoundError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "Item not found"})

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3NotFoundError):
            await client.get_product("missing_id")

    asyncio.run(run())


def test_error_500_retries_and_raises_server_error():
    """Test 500 internal server error retries before raising Channel3ServerError."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(500, json={"error": "Internal error"})

    config = Channel3Config(
        api_key="key",
        max_retries=2,
        backoff_factor=0.01,
    )
    client = make_mock_client(handler, config=config)

    async def run():
        with pytest.raises(Channel3ServerError):
            await client.search_products(query="chair")

    asyncio.run(run())
    assert attempts == 3  # initial + 2 retries


def test_error_network_connection_failure():
    """Test connection error raises Channel3NetworkError after retries."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("Connection refused by peer")

    config = Channel3Config(api_key="key", max_retries=1, backoff_factor=0.01)
    client = make_mock_client(handler, config=config)

    async def run():
        with pytest.raises(Channel3NetworkError):
            await client.search_products(query="lamp")

    asyncio.run(run())
    assert attempts == 2


def test_error_invalid_json_payload():
    """Test provider returning non-JSON HTML (e.g. cloudflare 502) raises Channel3ServerError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<html>Bad Gateway</html>", headers={"Content-Type": "text/html"})

    client = make_mock_client(handler)

    async def run():
        with pytest.raises(Channel3ServerError, match="invalid JSON"):
            await client.search_products(query="lamp")

    asyncio.run(run())
