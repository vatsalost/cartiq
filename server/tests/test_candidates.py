"""Tests for candidate product and offer retrieval."""


def test_candidate_retrieval(client, valid_request, sample_candidate):
    """Test 12: Candidate retrieval returns products and retailer offers."""
    res = client.get(f"/api/requests/{valid_request.id}/candidates")
    assert res.status_code == 200
    data = res.json()
    assert data["request_id"] == str(valid_request.id)
    assert len(data["candidates"]) == 1
    c = data["candidates"][0]
    assert c["title"] == sample_candidate.title
    assert c["provider_product_id"] == sample_candidate.provider_product_id
    assert len(c["offers"]) == 1
    assert c["offers"][0]["domain"] == "target.com"
    assert c["offers"][0]["price_amount"] == "34.99"


def test_candidate_ownership(client, valid_request, other_user):
    """Candidate retrieval blocked for other users."""
    headers = {"Authorization": f"Bearer {other_user.id}"}
    res = client.get(f"/api/requests/{valid_request.id}/candidates", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"
