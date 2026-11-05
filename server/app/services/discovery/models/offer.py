"""Normalized retailer offer model."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NormalizedOffer(BaseModel):
    """Represents a discrete retailer offer for a canonical product.

    All monetary amounts MUST use Decimal to eliminate float rounding errors.
    """

    model_config = ConfigDict(extra="ignore")

    offer_key: str = Field(
        description="Deterministic stable unique identifier for this specific retailer listing."
    )
    domain: str = Field(
        description="Clean, normalized retailer domain name (e.g., 'target.com', 'nike.com')."
    )
    price_amount: Decimal = Field(
        description="Current listing price as an exact Decimal."
    )
    currency: str = Field(
        description="3-letter ISO 4217 uppercase currency code (e.g., 'USD')."
    )
    availability: str = Field(
        description="Availability status (e.g., 'InStock', 'OutOfStock', 'Unknown')."
    )
    condition: str = Field(
        description="Condition status (e.g., 'new', 'used', 'refurbished', 'unknown')."
    )
    buy_url: str = Field(
        description="Direct affiliate-ready or canonical retailer buy link."
    )
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this offer was fetched or refreshed."
    )
    merchant_id: Optional[str] = Field(
        default=None,
        description="Channel3 internal merchant identifier if provided."
    )
    merchant_name: Optional[str] = Field(
        default=None,
        description="Human-readable merchant or seller name."
    )
    compare_at_price: Optional[Decimal] = Field(
        default=None,
        description="Original / strikethrough price if on sale."
    )
    commission_rate: Optional[Decimal] = Field(
        default=None,
        description="Affiliate commission percentage if available."
    )
    extra_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Preserved raw metadata from provider for audit without modification."
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if len(clean) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code, got: {v!r}")
        return clean

    @field_validator("price_amount", "compare_at_price", "commission_rate", mode="before")
    @classmethod
    def parse_decimal(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"Invalid decimal value: {v!r}") from e

    @field_validator("domain")
    @classmethod
    def clean_domain(cls, v: str) -> str:
        d = v.strip().lower()
        if d.startswith("http://"):
            d = d[7:]
        elif d.startswith("https://"):
            d = d[8:]
        if d.startswith("www."):
            d = d[4:]
        return d.split("/")[0].split(":")[0]
