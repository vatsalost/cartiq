"""Mandate Pydantic schemas and strict business validators."""

from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MandateBase(BaseModel):
    """Base fields for mandate validation."""

    total_budget: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        le=Decimal("100000.00"),
        description="Total spending budget allowed for this mandate",
    )
    per_item_cap: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        le=Decimal("100000.00"),
        description="Maximum allowed price for any single item",
    )
    currency: str = Field(
        "USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 3-letter uppercase currency code",
    )
    allowed_categories: List[str] = Field(
        ...,
        min_length=1,
        description="List of product categories allowed for purchase",
    )
    blocked_categories: Optional[List[str]] = Field(
        default_factory=list,
        description="Categories strictly prohibited",
    )
    allowed_retailers: Optional[List[str]] = Field(
        default_factory=list,
        description="Allowed retailer domains (e.g., target.com, amazon.com)",
    )
    max_quantity_per_product: int = Field(
        1,
        ge=1,
        le=50,
        description="Maximum quantity allowed per product",
    )
    price_tolerance_pct: Decimal = Field(
        Decimal("0.0000"),
        ge=Decimal("0.0000"),
        le=Decimal("0.5000"),
        description="Allowed price increase percentage before re-approval required (e.g. 0.05 for 5%)",
    )
    expires_at: datetime = Field(
        ...,
        description="Mandate expiration timestamp in UTC (must be in the future)",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[A-Z]{3}$", clean):
            raise ValueError("Currency must be a valid 3-letter uppercase ISO code (e.g., USD, EUR, GBP)")
        return clean

    @field_validator("allowed_categories")
    @classmethod
    def validate_allowed_categories(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            raise ValueError("allowed_categories cannot be empty.")
        cleaned = [c.strip().title() for c in v if c and c.strip()]
        if not cleaned:
            raise ValueError("allowed_categories must contain at least one valid category name.")
        for cat in cleaned:
            if not re.match(r"^[A-Za-z0-9\s\-&]+$", cat) or len(cat) > 50:
                raise ValueError(f"Invalid category name: '{cat}'.")
        return sorted(list(set(cleaned)))

    @field_validator("blocked_categories")
    @classmethod
    def validate_blocked_categories(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            return []
        cleaned = [c.strip().title() for c in v if c and c.strip()]
        for cat in cleaned:
            if not re.match(r"^[A-Za-z0-9\s\-&]+$", cat) or len(cat) > 50:
                raise ValueError(f"Invalid category name: '{cat}'.")
        return sorted(list(set(cleaned)))

    @field_validator("allowed_retailers")
    @classmethod
    def clean_retailers(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            return []
        domain_pattern = re.compile(
            r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
        )
        cleaned = []
        for r in v:
            domain = r.strip().lower()
            domain = re.sub(r"^https?://", "", domain)
            domain = domain.split("/")[0].split("?")[0].split(":")[0]
            if not domain or not domain_pattern.match(domain):
                raise ValueError(f"Invalid retailer domain format: '{r}'. Expected format: example.com")
            cleaned.append(domain)
        return sorted(list(set(cleaned)))

    @field_validator("expires_at")
    @classmethod
    def validate_future_expiry(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError("Mandate expiration time must be in the future.")
        return v

    @model_validator(mode="after")
    def validate_budget_and_categories(self) -> "MandateBase":
        # Per-item cap cannot exceed total budget
        if self.per_item_cap > self.total_budget:
            raise ValueError("per_item_cap cannot be greater than total_budget.")

        # Blocked categories cannot contradict allowed categories
        allowed_set = set(self.allowed_categories)
        blocked_set = set(self.blocked_categories or [])
        intersection = allowed_set.intersection(blocked_set)
        if intersection:
            raise ValueError(
                f"Blocked categories cannot overlap with allowed categories: {', '.join(intersection)}"
            )
        return self


class MandateCreate(MandateBase):
    """Payload to create or update spending mandate."""
    pass


class BudgetBreakdown(BaseModel):
    """Authoritative financial budget breakdown for a mandate."""

    mandate_id: uuid.UUID
    total_budget: Decimal
    captured_spending: Decimal
    active_reservations: Decimal
    available_budget: Decimal
    currency: str

    model_config = ConfigDict(from_attributes=True)

    def __lt__(self, other):
        if isinstance(other, BudgetBreakdown):
            return self.available_budget < other.available_budget
        return self.available_budget < other

    def __le__(self, other):
        if isinstance(other, BudgetBreakdown):
            return self.available_budget <= other.available_budget
        return self.available_budget <= other

    def __gt__(self, other):
        if isinstance(other, BudgetBreakdown):
            return self.available_budget > other.available_budget
        return self.available_budget > other

    def __ge__(self, other):
        if isinstance(other, BudgetBreakdown):
            return self.available_budget >= other.available_budget
        return self.available_budget >= other


class MandateValidationResult(BaseModel):
    """Structured validation output for mandate eligibility checks."""

    valid: bool
    mandate_id: Optional[uuid.UUID] = None
    version: Optional[int] = None
    status: Optional[str] = None
    is_expired: bool = False
    errors: List[str] = Field(default_factory=list)


def generate_mandate_summary(
    allowed_categories: List[str],
    total_budget: Decimal,
    per_item_cap: Decimal,
    currency: str,
    expires_at: datetime,
    allowed_retailers: Optional[List[str]] = None,
) -> str:
    """Generate human-readable summary description of the mandate rules."""
    cats = (
        " and ".join(allowed_categories)
        if len(allowed_categories) <= 2
        else f"{', '.join(allowed_categories[:-1])}, and {allowed_categories[-1]}"
    )
    ret_text = ""
    if allowed_retailers:
        rets = (
            " and ".join(allowed_retailers)
            if len(allowed_retailers) <= 2
            else f"{', '.join(allowed_retailers[:-1])}, and {allowed_retailers[-1]}"
        )
        ret_text = f" from {rets}"
    expiry_str = expires_at.strftime("%Y-%m-%d")
    return (
        f"The agent may recommend products in {cats}{ret_text}, with a total budget of "
        f"{total_budget} {currency} and a maximum of {per_item_cap} {currency} per item, until {expiry_str}."
    )


class MandateResponse(MandateBase):
    """Canonical mandate representation returned by server."""

    id: uuid.UUID
    user_id: uuid.UUID
    version: int
    status: str
    created_at: datetime
    available_budget: Optional[Decimal] = None
    captured_spending: Optional[Decimal] = None
    active_reservations: Optional[Decimal] = None
    summary_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
