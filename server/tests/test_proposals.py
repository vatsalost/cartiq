"""Tests for proposal inspection and PayPal order creation."""


def test_proposal_retrieval(client, sample_proposal):
    """Test proposal retrieval with embedded summaries."""
    res = client.get(f"/api/proposals/{sample_proposal.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(sample_proposal.id)
    assert data["unit_price_at_proposal"] == "34.99"
    assert data["currency"] == "USD"
    assert data["status"] == "pending"
    assert data["product"]["title"] == "Modern Adjustable Desk Lamp"
    assert data["offer"]["domain"] == "target.com"


def test_proposal_ownership(client, sample_proposal, other_user):
    """Test 13: Proposal ownership prevents cross-user access."""
    headers = {"Authorization": f"Bearer {other_user.id}"}
    res = client.get(f"/api/proposals/{sample_proposal.id}", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_stale_proposal_order_rejection(client, sample_proposal, db):
    """Test 14: Non-pending or stale proposal rejects order creation."""
    sample_proposal.status = "stale"
    db.commit()

    res = client.post(
        f"/api/proposals/{sample_proposal.id}/order",
        json={"checkout_attempt_id": "attempt_1"},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "PROPOSAL_STALE"


def test_paypal_order_creation_delegation(client, sample_proposal):
    """Test 15: Valid proposal creates internal and PayPal Sandbox order."""
    res = client.post(
        f"/api/proposals/{sample_proposal.id}/order",
        json={"checkout_attempt_id": "attempt_valid_123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "order_id" in data
    assert "paypal_order_id" in data
    assert data["status"] == "created"
    assert data["amount"] == "34.99"
    assert data["currency"] == "USD"
