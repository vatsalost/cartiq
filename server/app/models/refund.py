"""Refund model for tracking PayPal Sandbox refund operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, utc_now


class Refund(Base, UUIDPrimaryKeyMixin):
    """Refund transaction record."""

    __tablename__ = "refunds"

    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    paypal_refund_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    request_idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    order = relationship("Order", back_populates="refunds")
