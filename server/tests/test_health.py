"""Tests for health endpoint."""

from unittest.mock import patch


def test_health_endpoint_healthy(client):
    """Test 1: Health endpoint responds with 200 and connected database."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "version" in data
    # Ensure no credentials or sensitive info leaked
    assert "password" not in response.text.lower()
    assert "secret" not in response.text.lower()


def test_health_endpoint_db_failure(client):
    """Test 2: Database connectivity failure returns 503 degraded status."""
    with patch("server.app.api.routes.health.check_db_connectivity", return_value=False):
        response = client.get("/api/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"
