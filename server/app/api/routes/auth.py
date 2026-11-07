"""Authentication and session management API routes."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from server.app.api.dependencies import (
    get_auth_service,
    get_optional_current_user,
    require_active_user,
)
from server.app.core.config import settings
from server.app.core.rate_limit import auth_limiter, rate_limit
from server.app.core.security import AuthenticatedUser, parse_bearer_token
from server.app.schemas.auth import (
    AuthResponse,
    AuthStatusResponse,
    DemoLoginRequest,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    UserSafeProfile,
)
from server.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookie(response: Response, token: str, expires_at: datetime) -> None:
    """Set secure HTTP-only session cookie."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_EXPIRE_DAYS * 86400,
        expires=expires_at,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear session cookie upon logout."""
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )


def _get_client_metadata(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and User-Agent."""
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else None)
    )
    user_agent = request.headers.get("user-agent")
    return (client_ip, user_agent)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="Registers an account with email and password using Argon2id hashing.",
    dependencies=[Depends(rate_limit(auth_limiter))],
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    ip, ua = _get_client_metadata(request)
    user, token, session = auth_service.register_user(
        email=payload.email,
        password=payload.password,
        ip_address=ip,
        user_agent=ua,
    )
    _set_auth_cookie(response, token, session.expires_at)
    return AuthResponse(
        user=UserSafeProfile(
            id=user.id,
            email=user.email,
            status=user.status,
            is_active=user.is_active,
            authenticated=True,
        ),
        token=token,
        token_type="bearer",
        expires_at=session.expires_at,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticates credentials and rotates to a new cryptographically secure session.",
    dependencies=[Depends(rate_limit(auth_limiter))],
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    ip, ua = _get_client_metadata(request)
    user, token, session = auth_service.login_user(
        email=payload.email,
        password=payload.password,
        ip_address=ip,
        user_agent=ua,
    )
    _set_auth_cookie(response, token, session.expires_at)
    return AuthResponse(
        user=UserSafeProfile(
            id=user.id,
            email=user.email,
            status=user.status,
            is_active=user.is_active,
            authenticated=True,
        ),
        token=token,
        token_type="bearer",
        expires_at=session.expires_at,
    )


@router.post(
    "/demo",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Demo user authentication",
    description="Authenticates or seeds an isolated demo user. Strictly forbidden in production.",
)
async def login_demo(
    request: Request,
    response: Response,
    payload: Optional[DemoLoginRequest] = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    ip, ua = _get_client_metadata(request)
    demo_id = payload.demo_identifier if payload else None
    user, token, session = auth_service.login_demo_user(
        demo_identifier=demo_id,
        ip_address=ip,
        user_agent=ua,
    )
    _set_auth_cookie(response, token, session.expires_at)
    return AuthResponse(
        user=UserSafeProfile(
            id=user.id,
            email=user.email,
            status=user.status,
            is_active=user.is_active,
            authenticated=True,
        ),
        token=token,
        token_type="bearer",
        expires_at=session.expires_at,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Revokes current session in database and clears session cookie.",
)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_header = request.headers.get("Authorization")
    token = parse_bearer_token(auth_header) or request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        auth_service.logout_session(token)
    _clear_auth_cookie(response)
    return LogoutResponse(status="logged_out", message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserSafeProfile,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the authenticated user's safe profile. Requires valid active session.",
)
async def get_me(
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    return UserSafeProfile(
        id=current_user.id,
        email=current_user.email,
        status="active",
        is_active=current_user.is_active,
        authenticated=True,
    )


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check authentication status",
    description="Public endpoint to check if the caller has an active authenticated session.",
)
async def auth_status(
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
):
    if current_user:
        return AuthStatusResponse(
            authenticated=True,
            user=UserSafeProfile(
                id=current_user.id,
                email=current_user.email,
                status="active",
                is_active=current_user.is_active,
                authenticated=True,
            ),
        )
    return AuthStatusResponse(authenticated=False, user=None)
