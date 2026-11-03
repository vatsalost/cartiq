"""Order model for tracking PayPal checkout and captures."""

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
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Internal order linked to a proposal and PayPal transaction."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_created", "user_id", "created_at"),
    )

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    paypal_order_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    paypal_capture_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    create_request_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    capture_request_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False, index=True)
    budget_reserved: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    proposal = relationship("Proposal", back_populates="order")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
