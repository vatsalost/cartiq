"""Webhook events model for tracking and deduplicating PayPal notifications."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, utc_now


class WebhookEvent(Base, UUIDPrimaryKeyMixin):
    """Incoming PayPal webhook record for deduplication and audit."""

    __tablename__ = "webhook_events"

    provider_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
