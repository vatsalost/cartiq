"""Audit logging service implementing IAuditService."""

from typing import Any, Dict, Optional
import uuid
from sqlalchemy.orm import Session
from server.app.models.audit import AuditEvent


class AuditService:
    """Records audit logs to PostgreSQL for compliance and observability."""

    def __init__(self, db: Session):
        self.db = db

    def record_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        actor: str = "system",
        request_id: Optional[uuid.UUID] = None,
        proposal_id: Optional[uuid.UUID] = None,
        order_id: Optional[uuid.UUID] = None,
        decision: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            user_id=user_id,
            request_id=request_id,
            proposal_id=proposal_id,
            order_id=order_id,
            event_type=event_type,
            actor=actor,
            decision=decision,
            reason=reason,
            details=details or {},
        )
        self.db.add(event)
        self.db.commit()
        return event

    def get_events_for_user(
        self, target_user_id: uuid.UUID, caller_user_id: uuid.UUID, limit: int = 50
    ) -> list[AuditEvent]:
        """Fetch audit trail for a user ensuring strict ownership validation."""
        from sqlalchemy import select
        from server.app.core.errors import CartiAPIException, CartiErrorCode

        if target_user_id != caller_user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to view another user's audit records.",
                status_code=403,
            )

        stmt = (
            select(AuditEvent)
            .where(AuditEvent.user_id == caller_user_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
