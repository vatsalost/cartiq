"""Audit event history and compliance endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.app.api.dependencies import get_current_user, get_db
from server.app.core.security import AuthenticatedUser
from server.app.schemas.audit import AuditEventResponse
from server.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "/timeline",
    response_model=List[AuditEventResponse],
    summary="Get audit timeline for authenticated user",
    description="Returns chronological audit events, security checks, and financial milestones.",
)
async def get_audit_timeline(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    audit_svc = AuditService(db)
    events = audit_svc.get_events_for_user(
        target_user_id=current_user.id,
        caller_user_id=current_user.id,
        limit=50,
    )
    return events


@router.get(
    "",
    response_model=List[AuditEventResponse],
    summary="Get audit events for authenticated user",
    description="Alias to /audit/timeline for listing audit trail events.",
)
async def list_audit_events(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await get_audit_timeline(current_user=current_user, db=db)
