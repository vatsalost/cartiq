"""Tests for spending mandate creation, validation, and versioning."""

from datetime import datetime, timedelta, timezone


def test_mandate_creation_and_retrieval(client, test_user):
    """Test 3: Valid mandate creation and retrieval."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    payload = {
        "total_budget": "150.00",
        "per_item_cap": "50.00",
        "currency": "USD",
        "allowed_categories": ["Electronics", "Home"],
        "blocked_categories": ["Clothing"],
        "allowed_retailers": ["https://target.com/deals", "amazon.com"],
        "max_quantity_per_product": 2,
        "price_tolerance_pct": "0.05",
        "expires_at": future_date,
    }

    create_res = client.post("/api/mandates", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["total_budget"] == "150.00"
    assert created_data["per_item_cap"] == "50.00"
    assert created_data["currency"] == "USD"
    assert created_data["version"] == 1
    assert created_data["status"] == "active"
    # Verify retailers normalized to domains
    assert "target.com" in created_data["allowed_retailers"]
    assert "amazon.com" in created_data["allowed_retailers"]

    # Retrieve current active mandate
    get_res = client.get("/api/mandates/current")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created_data["id"]


def test_mandate_invalid_values(client):
    """Test 4: Invalid mandate values fail with validation errors."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # 1. Cap greater than budget
    res = client.post(
        "/api/mandates",
        json={
            "total_budget": "50.00",
            "per_item_cap": "100.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
    )
    assert res.status_code == 422
    assert "per_item_cap cannot be greater than total_budget" in res.text

    # 2. Expiry in the past
    res2 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": past_date,
        },
    )
    assert res2.status_code == 422
    assert "must be in the future" in res2.text

    # 3. Overlapping allowed and blocked categories
    res3 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home", "Electronics"],
            "blocked_categories": ["Home"],
            "expires_at": future_date,
        },
    )
    assert res3.status_code == 422
    assert "cannot overlap" in res3.text


def test_mandate_versioning(client, test_user):
    """Test 5: Mandate updates increment version and supersede previous."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # Version 1
    res1 = client.post(
        "/api/mandates",
        json={
            "total_budget": "100.00",
            "per_item_cap": "50.00",
            "currency": "USD",
            "allowed_categories": ["Home"],
            "expires_at": future_date,
        },
    )
    assert res1.status_code == 201
    assert res1.json()["version"] == 1

    # Version 2
    res2 = client.post(
        "/api/mandates",
        json={
            "total_budget": "200.00",
            "per_item_cap": "80.00",
            "currency": "USD",
            "allowed_categories": ["Home", "Electronics"],
            "expires_at": future_date,
        },
    )
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["version"] == 2
    assert data2["total_budget"] == "200.00"

    # Current should return version 2
    current_res = client.get("/api/mandates/current")
    assert current_res.json()["version"] == 2
