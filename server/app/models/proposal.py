"""Purchase proposal model."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    Uuid,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.db.session import Base
from server.app.models.base import UUIDPrimaryKeyMixin, utc_now


class Proposal(Base, UUIDPrimaryKeyMixin):
    """Immutable proposal snapshot ready for user review."""

    __tablename__ = "proposals"
    __table_args__ = (
        Index("ix_proposals_user_status", "user_id", "status"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_offers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_at_proposal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal_at_proposal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    guardrail_result: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    verification_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    request = relationship("ShoppingRequest", back_populates="proposals")
    mandate = relationship("Mandate")
    candidate = relationship("Candidate")
    offer = relationship("CandidateOffer")
    order = relationship("Order", back_populates="proposal", uselist=False)
