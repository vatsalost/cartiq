"""Tests for malformed payloads and rate limiting."""

from server.app.core.rate_limit import request_creation_limiter


def test_malformed_payload_validation(client):
    """Test 21: Malformed payloads return structured 422 VALIDATION_ERROR envelope."""
    # Send empty body or invalid types
    res = client.post("/api/requests", json={"text": "a"})  # min_length=3
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "validation_errors" in data["error"]["details"]


def test_rate_limiting_enforcement(client, active_mandate):
    """Test 22: Exceeding request creation limit returns 429 RATE_LIMIT_EXCEEDED."""
    payload = {"text": "Search for computer mouse under $20"}

    # Simulate exhausting the rate limiter
    client_key = "testclient:/api/requests"
    request_creation_limiter.requests[client_key] = [9999999999.0] * 10

    res = client.post("/api/requests", json=payload)
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    # Reset limiter for subsequent tests
    request_creation_limiter.requests.clear()
