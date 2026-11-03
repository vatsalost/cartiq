"""FastAPI dependency injection providers."""

from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.core.security import (
    AuthenticatedUser,
    resolve_optional_user,
    resolve_user_from_request,
)
from server.app.db.session import get_db
from server.app.services.auth_service import AuthService
from server.app.services.candidate_service import CandidateService
from server.app.services.mandate_service import MandateService
from server.app.services.order_service import OrderService
from server.app.services.proposal_service import ProposalService
from server.app.services.request_service import RequestService
from server.app.services.webhook_service import WebhookService


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> AuthenticatedUser:
    """Dependency to retrieve and validate the authenticated user from the request."""
    return resolve_user_from_request(request, db=db)


def get_optional_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[AuthenticatedUser]:
    """Dependency to retrieve current user if authenticated, without failing if absent."""
    return resolve_optional_user(request, db=db)


def require_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Dependency ensuring authenticated user is active."""
    if not current_user.is_active:
        raise CartiAPIException(
            code=CartiErrorCode.ACCESS_DENIED,
            message="Account is inactive or disabled.",
            status_code=403,
            retryable=False,
        )
    return current_user


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide initialized AuthService instance."""
    return AuthService(db)


def get_mandate_service(db: Session = Depends(get_db)) -> MandateService:
    """Provide initialized MandateService instance."""
    return MandateService(db)


def get_request_service(db: Session = Depends(get_db)) -> RequestService:
    """Provide initialized RequestService instance."""
    return RequestService(db)


def get_candidate_service(db: Session = Depends(get_db)) -> CandidateService:
    """Provide initialized CandidateService instance."""
    return CandidateService(db)


def get_proposal_service(db: Session = Depends(get_db)) -> ProposalService:
    """Provide initialized ProposalService instance."""
    return ProposalService(db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Provide initialized OrderService instance."""
    return OrderService(db)


def get_webhook_service(db: Session = Depends(get_db)) -> WebhookService:
    """Provide initialized WebhookService instance."""
    return WebhookService(db)
