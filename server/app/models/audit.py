"""Audit event model for compliance and security observability."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    JSON,
    Uuid,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, utc_now


class AuditEvent(Base, UUIDPrimaryKeyMixin):
    """Audit log entry tracking decisions, checks, and payments."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_user_time", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    proposal_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(32), default="system", nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
