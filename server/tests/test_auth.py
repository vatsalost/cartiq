"""Comprehensive tests for Backend Module B2: Authentication and Session Lifecycle."""

from datetime import datetime, timedelta, timezone
import hashlib
import uuid
import pytest
from sqlalchemy import select
from server.app.core.config import settings
from server.app.core.rate_limit import auth_limiter
from server.app.models.session import UserSession
from server.app.models.user import User


@pytest.fixture(autouse=True)
def reset_limiters():
    """Reset auth rate limiter before every test."""
    auth_limiter.reset()
    yield
    auth_limiter.reset()


def test_user_registration_success(client, db):
    """Test standard registration with Argon2id hash and session cookie."""
    payload = {
        "email": "alice@carti.local",
        "password": "SecurePassword123!",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@carti.local"
    assert data["user"]["is_active"] is True
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]

    # Verify cookie was set
    assert settings.SESSION_COOKIE_NAME in res.cookies

    # Verify database persistence
    user = db.scalars(select(User).where(User.email == "alice@carti.local")).first()
    assert user is not None
    assert user.password_hash is not None
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != "SecurePassword123!"

    # Verify session record in db
    raw_token = data["token"]
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    session = db.scalars(select(UserSession).where(UserSession.token_hash == expected_hash)).first()
    assert session is not None
    assert session.user_id == user.id
    assert session.revoked_at is None


def test_user_registration_validation_errors(client):
    """Test invalid email and weak password rejection during registration."""
    # Invalid email
    res1 = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "SecurePassword123!"},
    )
    assert res1.status_code == 422

    # Password too short
    res2 = client.post(
        "/api/auth/register",
        json={"email": "test@carti.local", "password": "short"},
    )
    assert res2.status_code == 422

    # Password without digits
    res3 = client.post(
        "/api/auth/register",
        json={"email": "test@carti.local", "password": "onlylettersandnosymbols"},
    )
    assert res3.status_code == 422


def test_user_registration_duplicate_email(client):
    """Test duplicate registration returns 409 conflict."""
    payload = {
        "email": "duplicate@carti.local",
        "password": "SecurePassword123!",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "already exists" in res2.json()["error"]["message"]


def test_login_success_and_session_rotation(client, db):
    """Test login generates fresh session token and rotates session."""
    # 1. Register user
    reg_payload = {"email": "bob@carti.local", "password": "Password1234!"}
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    first_token = reg_res.json()["token"]

    # 2. Login
    login_payload = {"email": "bob@carti.local", "password": "Password1234!"}
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    second_token = login_data["token"]

    # Tokens must be rotated (distinct)
    assert first_token != second_token
    assert login_data["user"]["email"] == "bob@carti.local"

    # Both sessions should be in db
    first_hash = hashlib.sha256(first_token.encode("utf-8")).hexdigest()
    second_hash = hashlib.sha256(second_token.encode("utf-8")).hexdigest()
    s1 = db.scalars(select(UserSession).where(UserSession.token_hash == first_hash)).first()
    s2 = db.scalars(select(UserSession).where(UserSession.token_hash == second_hash)).first()
    assert s1 is not None
    assert s2 is not None


def test_login_invalid_credentials(client):
    """Test invalid password and unknown user rejection."""
    # Unknown user
    res1 = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@carti.local", "password": "Password123!"},
    )
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # Register user
    client.post(
        "/api/auth/register",
        json={"email": "valid@carti.local", "password": "Password123!"},
    )

    # Wrong password
    res2 = client.post(
        "/api/auth/login",
        json={"email": "valid@carti.local", "password": "WrongPassword123!"},
    )
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_login_inactive_user_rejection(client, db):
    """Test inactive or disabled user is rejected with 403."""
    reg_payload = {"email": "disabled@carti.local", "password": "Password123!"}
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201

    # Disable user
    user = db.scalars(select(User).where(User.email == "disabled@carti.local")).first()
    user.is_active = False
    user.status = "suspended"
    db.commit()

    # Attempt login
    login_res = client.post("/api/auth/login", json=reg_payload)
    assert login_res.status_code == 403
    assert login_res.json()["error"]["code"] == "ACCESS_DENIED"


def test_demo_login_allowed_in_dev_and_isolated(client, db):
    """Test demo login in non-production environments with isolated identities."""
    res1 = client.post("/api/auth/demo", json={"demo_identifier": "demo-buyer-1"})
    assert res1.status_code == 200
    token1 = res1.json()["token"]
    user1_id = res1.json()["user"]["id"]

    res2 = client.post("/api/auth/demo", json={"demo_identifier": "demo-buyer-2"})
    assert res2.status_code == 200
    token2 = res2.json()["token"]
    user2_id = res2.json()["user"]["id"]

    # Distinct users for distinct demo identifiers
    assert user1_id != user2_id
    assert token1 != token2


def test_demo_login_blocked_in_production(client, monkeypatch):
    """Verify demo login is strictly blocked when APP_ENV == 'production'."""
    monkeypatch.setattr(settings, "APP_ENV", "production")
    res = client.post("/api/auth/demo", json={})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCESS_DENIED"


def test_logout_and_session_revocation(client, db):
    """Test session revocation upon logout."""
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "logout-test@carti.local", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    # Check active session before logout
    session = db.scalars(select(UserSession).where(UserSession.token_hash == token_hash)).first()
    assert session.revoked_at is None

    # Call logout
    logout_res = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"

    # Refresh session from db
    db.refresh(session)
    assert session.revoked_at is not None

    # Subsequent access with revoked token must fail with 401
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 401
    assert "revoked" in me_res.json()["error"]["message"].lower()


def test_session_expiration(client, db):
    """Test expired session token is rejected with 401."""
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "expire-test@carti.local", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    # Manually expire the session in the database
    session = db.scalars(select(UserSession).where(UserSession.token_hash == token_hash)).first()
    session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    # Access endpoint with expired session
    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert "expired" in res.json()["error"]["message"].lower()


def test_auth_me_endpoint(client):
    """Test /api/auth/me returns profile for active session."""
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "me-test@carti.local", "password": "Password123!"},
    )
    token = reg_res.json()["token"]

    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "me-test@carti.local"
    assert data["authenticated"] is True
    assert data["is_active"] is True


def test_auth_status_endpoint(client):
    """Test public /api/auth/status does not throw 401."""
    # When unauthenticated
    res1 = client.get(
        "/api/auth/status",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert res1.status_code == 200
    assert res1.json()["authenticated"] is False
    assert res1.json()["user"] is None

    # When authenticated
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "status-test@carti.local", "password": "Password123!"},
    )
    token = reg_res.json()["token"]

    res2 = client.get(
        "/api/auth/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    assert res2.json()["authenticated"] is True
    assert res2.json()["user"]["email"] == "status-test@carti.local"


def test_auth_via_session_cookie(client):
    """Test authenticated endpoints work seamlessly using session cookie."""
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "cookie-test@carti.local", "password": "Password123!"},
    )
    assert reg_res.status_code == 201
    assert settings.SESSION_COOKIE_NAME in client.cookies

    # Access /api/auth/me without Authorization header (relies on client cookie jar)
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "cookie-test@carti.local"


def test_auth_rate_limiting(client):
    """Verify auth endpoints enforce sliding window rate limiter (max 5/min)."""
    # 5 attempts allowed
    for i in range(5):
        res = client.post(
            "/api/auth/login",
            json={"email": f"ratelimit{i}@carti.local", "password": "Password123!"},
        )
        # Should be 401 (auth failure), not 429
        assert res.status_code == 401

    # 6th attempt should be blocked with 429
    res_blocked = client.post(
        "/api/auth/login",
        json={"email": "ratelimit_blocked@carti.local", "password": "Password123!"},
    )
    assert res_blocked.status_code == 429
    assert res_blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

