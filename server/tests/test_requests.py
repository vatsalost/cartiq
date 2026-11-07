"""Tests for shopping requests, ownership, cancellation, and SSE streaming."""

import uuid


def test_request_creation_without_mandate(client, test_user):
    """Test 6: Request creation without an active mandate returns 404."""
    response = client.post(
        "/api/requests",
        json={"text": "Find a modern warm desk lamp"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "MANDATE_NOT_FOUND"


def test_valid_request_creation(client, active_mandate):
    """Test 7: Valid request creation returns 202 Accepted and stream URL."""
    payload = {
        "text": "Find a warm-light adjustable desk lamp under $40",
        "filters": {
            "category": "Home",
            "max_price": "40.00",
            "currency": "USD",
        },
    }
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "queued"
    assert data["stream_url"] == f"/api/requests/{data['request_id']}/stream"

    # Status check
    status_res = client.get(f"/api/requests/{data['request_id']}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["request_text"] == payload["text"]
    assert status_data["mandate_id"] == str(active_mandate.id)


def test_request_ownership(client, valid_request, other_user):
    """Test 8: Request ownership prevents unauthorized users from accessing."""
    # Request belonging to test_user accessed by other_user
    headers = {"Authorization": f"Bearer {other_user.id}"}
    response = client.get(f"/api/requests/{valid_request.id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCESS_DENIED"


def test_sse_event_streaming_and_reconnection(client, valid_request, db):
    """Test 9 & 10: SSE event streaming and reconnection via last_event_id."""
    from server.app.models.request import RequestEvent

    # Seed events
    ev1 = RequestEvent(
        request_id=valid_request.id,
        event_type="request_started",
        payload={"step": "request_started", "progress": 10},
    )
    ev2 = RequestEvent(
        request_id=valid_request.id,
        event_type="proposal_ready",
        payload={"step": "proposal_ready", "proposal_id": str(uuid.uuid4())},
    )
    db.add_all([ev1, ev2])
    db.commit()

    # Initial stream (should receive both events and close on proposal_ready)
    res = client.get(f"/api/requests/{valid_request.id}/stream")
    assert res.status_code == 200
    assert "event: request_started" in res.text
    assert "event: proposal_ready" in res.text

    # Reconnect using last_event_id=1 (should only replay ev2)
    reconnect_res = client.get(
        f"/api/requests/{valid_request.id}/stream?last_event_id={ev1.id}"
    )
    assert reconnect_res.status_code == 200
    assert "event: request_started" not in reconnect_res.text
    assert "event: proposal_ready" in reconnect_res.text


def test_request_cancellation(client, valid_request):
    """Test 11: Request cancellation marks state cancelled."""
    cancel_res = client.post(f"/api/requests/{valid_request.id}/cancel")
    assert cancel_res.status_code == 200
    data = cancel_res.json()
    assert data["status"] == "cancelled"

    # Verify status in database
    get_res = client.get(f"/api/requests/{valid_request.id}")
    assert get_res.json()["status"] == "cancelled"
