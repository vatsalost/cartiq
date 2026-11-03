"""Candidate product and offer models."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
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


class Candidate(Base, UUIDPrimaryKeyMixin):
    """Product candidate found during agent search."""

    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_request_provider", "request_id", "provider_product_id"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    rank_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    rank_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejected_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    request = relationship("ShoppingRequest", back_populates="candidates")
    offers = relationship("CandidateOffer", back_populates="candidate", cascade="all, delete-orphan")


class CandidateOffer(Base, UUIDPrimaryKeyMixin):
    """Specific retailer offer for a candidate product."""

    __tablename__ = "candidate_offers"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_offer_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    buy_url: Mapped[str] = mapped_column(Text, nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    availability: Mapped[str] = mapped_column(String(32), default="InStock", nullable=False)
    condition: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    variant_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="offers")
