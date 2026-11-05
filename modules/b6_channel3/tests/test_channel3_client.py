"""Tests for Channel3 low-level HTTP client and client initialization."""

import asyncio
import json
import httpx
import pytest
from modules.b6_channel3.client.authentication import Channel3Auth
from modules.b6_channel3.client.channel3_client import Channel3Client
from modules.b6_channel3.client.http_client import Channel3HTTPClient
from modules.b6_channel3.config import Channel3Config
from modules.b6_channel3.exceptions import Channel3AuthError


def test_auth_header_injection(test_config: Channel3Config):
    """Test x-api-key and content headers are properly set."""
    auth = Channel3Auth(test_config.api_key)
    headers = auth.get_auth_headers()
    assert headers["x-api-key"] == "test_ch3_secret_api_key_12345"
    assert headers["Content-Type"] == "application/json"
    assert "User-Agent" in headers


def test_missing_api_key_raises():
    """Test client raises Channel3AuthError when API key is completely absent."""
    cfg = Channel3Config(api_key=None)
    auth = Channel3Auth(cfg.api_key)
    with pytest.raises(Channel3AuthError):
        auth.get_auth_headers()


def test_http_client_context_manager(test_config: Channel3Config):
    """Test async context manager on Channel3Client properly initializes and closes."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"products": []})

    transport = httpx.MockTransport(handler)
    http_cli = Channel3HTTPClient(config=test_config, transport=transport)

    async def run():
        async with Channel3Client(config=test_config, http_client=http_cli) as client:
            res = await client.search_products(query="laptop")
            assert res == []

    asyncio.run(run())


def test_client_header_captured_in_request(test_config: Channel3Config):
    """Verify request outgoing headers received by mock transport."""
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_headers
        captured_headers = dict(request.headers)
        return httpx.Response(200, json={"products": []})

    transport = httpx.MockTransport(handler)
    http_cli = Channel3HTTPClient(config=test_config, transport=transport)
    client = Channel3Client(config=test_config, http_client=http_cli)

    async def run():
        await client.search_products(query="shoes")

    asyncio.run(run())
    assert captured_headers.get("x-api-key") == "test_ch3_secret_api_key_12345"
    assert captured_headers.get("content-type") == "application/json"
