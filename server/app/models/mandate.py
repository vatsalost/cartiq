"""Mandate model enforcing boundaries for shopping requests."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    JSON,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, utc_now


class Mandate(Base, UUIDPrimaryKeyMixin):
    """Spending mandate version defining agent policy."""

    __tablename__ = "mandates"
    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_mandates_user_version"),
        Index("ix_mandates_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    per_item_cap: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    allowed_categories: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    blocked_categories: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    allowed_retailers: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    max_quantity_per_product: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_tolerance_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0.0000"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="mandates")
    requests = relationship("ShoppingRequest", back_populates="mandate")
