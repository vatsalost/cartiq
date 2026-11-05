"""Authentication, session validation, and ownership utilities."""

from datetime import datetime, timezone
import hashlib
from typing import Optional
import uuid
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.session import UserSession


class AuthenticatedUser(BaseModel):
    """User representation after authentication."""

    id: uuid.UUID
    email: str
    is_demo: bool = False
    is_active: bool = True
    session_id: Optional[uuid.UUID] = None


def parse_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """Extract token string from Authorization: Bearer <token> header."""
    if not auth_header:
        return None
    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_demo_user() -> AuthenticatedUser:
    """Return default seeded demo user for local development and tests."""
    return AuthenticatedUser(
        id=uuid.UUID(settings.DEMO_USER_ID),
        email=settings.DEMO_USER_EMAIL,
        is_demo=True,
        is_active=True,
    )


def resolve_user_from_request(
    request: Request, db: Optional[Session] = None
) -> AuthenticatedUser:
    """
    Resolve and validate user from Authorization header, session cookie, or demo fallback.
    Never trusts a user_id from the request body or path.
    """
    auth_header = request.headers.get("Authorization")
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if auth_header is not None:
        token = parse_bearer_token(auth_header)
        if not token:
            raise CartiAPIException(
                code=CartiErrorCode.AUTHENTICATION_REQUIRED,
                message="Invalid or malformed Authorization header.",
                status_code=401,
                retryable=False,
            )
        active_token = token
    elif cookie_token:
        active_token = cookie_token
    else:
        active_token = None

    # 1. Custom token resolution
    if active_token:
        # A. Database session lookup by token hash
        if db is not None:
            token_hash = hashlib.sha256(active_token.encode("utf-8")).hexdigest()
            session = db.scalars(
                select(UserSession).where(UserSession.token_hash == token_hash)
            ).first()

            if session:
                if session.revoked_at is not None:
                    raise CartiAPIException(
                        code=CartiErrorCode.AUTHENTICATION_REQUIRED,
                        message="Session has been revoked. Please sign in again.",
                        status_code=401,
                        retryable=False,
                    )

                now = datetime.now(timezone.utc)
                expires_at = session.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at <= now:
                    raise CartiAPIException(
                        code=CartiErrorCode.AUTHENTICATION_REQUIRED,
                        message="Session has expired. Please sign in again.",
                        status_code=401,
                        retryable=False,
                    )

                user = session.user
                if not user or not user.is_active or user.status != "active":
                    raise CartiAPIException(
                        code=CartiErrorCode.ACCESS_DENIED,
                        message="Account is disabled or inactive.",
                        status_code=403,
                        retryable=False,
                    )

                session.last_activity_at = now
                db.commit()

                return AuthenticatedUser(
                    id=user.id,
                    email=user.email,
                    is_demo=False,
                    is_active=user.is_active,
                    session_id=session.id,
                )

        # B. Check explicit demo tokens in allowed environments
        if active_token in ("demo-token", "test-token"):
            if settings.is_demo_allowed():
                return get_demo_user()
            raise CartiAPIException(
                code=CartiErrorCode.AUTHENTICATION_REQUIRED,
                message="Demo access is disabled.",
                status_code=401,
                retryable=False,
            )

        # C. Direct UUID or prefixed token (allowed only when demo/dev is enabled for testing)
        if settings.is_demo_allowed():
            try:
                if active_token.startswith("user_"):
                    raw_id = active_token.replace("user_", "")
                    user_id = uuid.UUID(raw_id)
                    return AuthenticatedUser(
                        id=user_id,
                        email=f"user_{raw_id[:8]}@carti.local",
                        is_demo=False,
                        is_active=True,
                    )
                user_id = uuid.UUID(active_token)
                return AuthenticatedUser(
                    id=user_id,
                    email=f"user_{str(user_id)[:8]}@carti.local",
                    is_demo=False,
                    is_active=True,
                )
            except ValueError:
                pass

        raise CartiAPIException(
            code=CartiErrorCode.AUTHENTICATION_REQUIRED,
            message="Invalid or expired authentication credentials.",
            status_code=401,
            retryable=False,
        )

    # 2. Demo user fallback if enabled in settings and no token provided
    if settings.is_demo_allowed() and settings.DEMO_USER_ENABLED:
        return get_demo_user()

    # 3. Otherwise authentication required
    raise CartiAPIException(
        code=CartiErrorCode.AUTHENTICATION_REQUIRED,
        message="Authentication required. Please sign in or provide a valid session.",
        status_code=401,
        retryable=False,
    )


def resolve_optional_user(
    request: Request, db: Optional[Session] = None
) -> Optional[AuthenticatedUser]:
    """Resolve current user if credentials present, otherwise return None without error."""
    try:
        return resolve_user_from_request(request, db=db)
    except CartiAPIException:
        return None


def verify_resource_ownership(
    resource_user_id: uuid.UUID,
    current_user: AuthenticatedUser,
    resource_name: str = "resource",
) -> None:
    """Ensure that the authenticated user owns the resource."""
    if resource_user_id != current_user.id:
        raise CartiAPIException(
            code=CartiErrorCode.ACCESS_DENIED,
            message="Access denied. You do not have permission to access this resource.",
            status_code=403,
            retryable=False,
            details={"resource": resource_name},
        )
