"""Shopping request and SSE progress event models."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Uuid,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, utc_now


class ShoppingRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Shopping request initiated by the user."""

    __tablename__ = "requests"
    __table_args__ = (
        Index("ix_requests_user_created", "user_id", "created_at"),
        Index("ix_requests_status_locked", "status", "locked_until"),
        Index("ix_requests_user_client_id", "user_id", "client_request_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mandate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mandates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_intent: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, index=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Lifecycle, worker lease & retry tracking
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    locked_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="requests")
    mandate = relationship("Mandate", back_populates="requests")
    events = relationship("RequestEvent", back_populates="request", cascade="all, delete-orphan", order_by="RequestEvent.id")
    candidates = relationship("Candidate", back_populates="request", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="request", cascade="all, delete-orphan")


class RequestEvent(Base):
    """Event log entry for SSE progress streaming."""

    __tablename__ = "request_events"
    __table_args__ = (
        Index("ix_request_events_request_seq", "request_id", "id"),
    )

    id: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger, "postgresql"),
        primary_key=True,
        autoincrement=True,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    request = relationship("ShoppingRequest", back_populates="events")
