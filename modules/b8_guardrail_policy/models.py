"""
Data models for Module B8 — Deterministic Guardrail & Policy Engine.

B8 consumes data contracts from B7 (MandateSnapshot, CandidateOption, RankedCandidate)
and produces authoritative PolicyDecision objects consumed by B9 (Proposal Service).

Design rules:
- All monetary values use Decimal (no float arithmetic).
- Decision states are deterministic enumerations — never probabilistic.
- An LLM must never produce or modify a PolicyDecision.
- B9 must treat REJECTED and UNABLE_TO_DETERMINE as non-approvable.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Decision state enumeration
# ---------------------------------------------------------------------------

class PolicyDecisionStatus(StrEnum):
    """Authoritative policy decision outcome.

    - APPROVED:            All applicable policy rules evaluated and passed.
    - REJECTED:            One or more mandatory policy rules failed.
    - INVALID_INPUT:       Structurally invalid or missing required input data.
    - UNABLE_TO_DETERMINE: Mandate or policy data missing/inconsistent; cannot safely approve.
    """

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INVALID_INPUT = "INVALID_INPUT"
    UNABLE_TO_DETERMINE = "UNABLE_TO_DETERMINE"


# ---------------------------------------------------------------------------
# Policy violation codes
# ---------------------------------------------------------------------------

class PolicyViolationCode(StrEnum):
    """Specific, structured policy violation codes."""

    # Mandate lifecycle
    MANDATE_MISSING = "MANDATE_MISSING"
    MANDATE_EXPIRED = "MANDATE_EXPIRED"
    MANDATE_INVALID_STATUS = "MANDATE_INVALID_STATUS"
    MANDATE_CURRENCY_MISSING = "MANDATE_CURRENCY_MISSING"

    # Budget / spending limits
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    PER_ITEM_CAP_EXCEEDED = "PER_ITEM_CAP_EXCEEDED"
    INSUFFICIENT_AVAILABLE_BUDGET = "INSUFFICIENT_AVAILABLE_BUDGET"

    # Category constraints
    BLOCKED_CATEGORY = "BLOCKED_CATEGORY"
    CATEGORY_NOT_ALLOWED = "CATEGORY_NOT_ALLOWED"

    # Retailer constraints
    RETAILER_NOT_ALLOWED = "RETAILER_NOT_ALLOWED"

    # Quantity constraints
    QUANTITY_EXCEEDED = "QUANTITY_EXCEEDED"

    # Currency
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"

    # Offer / product data
    INVALID_PRICE = "INVALID_PRICE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    INVALID_OFFER_DATA = "INVALID_OFFER_DATA"
    INVALID_PRODUCT_DATA = "INVALID_PRODUCT_DATA"
    MISSING_REQUIRED_ATTRIBUTE = "MISSING_REQUIRED_ATTRIBUTE"
    WRONG_CONDITION = "WRONG_CONDITION"
    STALE_OFFER_DATA = "STALE_OFFER_DATA"

    # Proposal-level
    PRICE_TOLERANCE_EXCEEDED = "PRICE_TOLERANCE_EXCEEDED"


# ---------------------------------------------------------------------------
# Individual rule result
# ---------------------------------------------------------------------------

class PolicyRuleResult(BaseModel):
    """Traceable result for a single policy rule evaluation.

    Every rule produces one of these records so decisions are fully auditable.
    """

    model_config = ConfigDict(extra="ignore")

    rule_name: str = Field(description="Human-readable name of the evaluated policy rule.")
    passed: bool = Field(description="Whether this rule passed (True) or was violated (False).")
    violation_code: Optional[PolicyViolationCode] = Field(
        default=None,
        description="Structured violation code when the rule failed.",
    )
    detail: str = Field(description="Factual, traceable description of the evaluation result.")


# ---------------------------------------------------------------------------
# Authoritative policy decision (produced by B8, consumed by B9)
# ---------------------------------------------------------------------------

class PolicyDecision(BaseModel):
    """Authoritative, deterministic policy decision produced by B8.

    B9 (Proposal Service) MUST consume this model and MUST NOT treat
    REJECTED or UNABLE_TO_DETERMINE as approved under any circumstance.

    This model is intentionally immutable after creation — downstream modules
    must not mutate its fields.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    decision_id: str = Field(
        description="Unique identifier for this specific policy evaluation (UUID).",
    )
    status: PolicyDecisionStatus = Field(
        description="Authoritative decision outcome.",
    )
    candidate_id: Optional[str] = Field(
        default=None,
        description="Identifier of the evaluated candidate option (product_id:offer_key).",
    )
    offer_key: Optional[str] = Field(
        default=None,
        description="Offer key of the evaluated retailer offer.",
    )
    rule_results: list[PolicyRuleResult] = Field(
        default_factory=list,
        description="Ordered list of individual rule evaluation results for full traceability.",
    )
    violations: list[PolicyViolationCode] = Field(
        default_factory=list,
        description="All violation codes from failed rules — empty when APPROVED.",
    )
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable rejection reason strings aligned with violations.",
    )
    evaluated_price: Optional[Decimal] = Field(
        default=None,
        description="Offer price amount that was evaluated (Decimal).",
    )
    evaluated_currency: Optional[str] = Field(
        default=None,
        description="Currency of the evaluated offer.",
    )
    evaluated_quantity: Optional[int] = Field(
        default=None,
        description="Quantity evaluated in the purchase proposal.",
    )
    mandate_status_at_evaluation: Optional[str] = Field(
        default=None,
        description="Mandate lifecycle status at time of evaluation.",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this decision was produced.",
    )

    @property
    def is_approved(self) -> bool:
        """Convenience accessor — True only when status is APPROVED."""
        return self.status == PolicyDecisionStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        """True when status is REJECTED (hard policy violation)."""
        return self.status == PolicyDecisionStatus.REJECTED

    @property
    def is_safe_to_proceed(self) -> bool:
        """False for any non-APPROVED decision. B9 must check this before proceeding."""
        return self.status == PolicyDecisionStatus.APPROVED


# ---------------------------------------------------------------------------
# Proposal evaluation request (input from B9 to B8)
# ---------------------------------------------------------------------------

class ProposalEvaluationRequest(BaseModel):
    """Input contract for evaluating a proposed purchase action.

    B9 submits this to B8 to request authoritative policy validation before
    any PayPal order creation or budget reservation.
    """

    model_config = ConfigDict(extra="ignore")

    candidate_id: str = Field(description="Unique candidate identifier (product_id:offer_key).")
    product_id: str = Field(description="Canonical Channel3 product identifier.")
    offer_key: str = Field(description="Deterministic retailer offer key.")
    product_title: str = Field(description="Product display title.")
    category: Optional[str] = Field(default=None, description="Product category string.")
    domain: str = Field(description="Retailer domain (e.g. 'target.com').")
    buy_url: str = Field(description="Affiliate or direct retailer URL.")
    price_amount: Decimal = Field(description="Exact offer price as Decimal.")
    currency: str = Field(description="3-letter ISO 4217 currency code.")
    availability: str = Field(description="Stock availability status string.")
    condition: str = Field(default="new", description="Product condition.")
    quantity: int = Field(default=1, ge=1, description="Requested purchase quantity.")
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Product attributes for required-attribute validation.",
    )
    observed_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when offer was last observed/fetched.",
    )
    b7_ranking_score: Optional[float] = Field(
        default=None,
        description=(
            "Optional B7 ranking score. PROVIDED FOR REFERENCE ONLY. "
            "B8 never uses this score to authorize or reject a proposal."
        ),
    )

    @field_validator("price_amount", mode="before")
    @classmethod
    def parse_price(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as exc:
            raise ValueError(f"Invalid price value: {v!r}") from exc

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if len(clean) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code: {v!r}")
        return clean

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity must be at least 1.")
        return v


# ---------------------------------------------------------------------------
# Mandate snapshot (re-exported for B8 consumers; consumed from B7 contract)
# ---------------------------------------------------------------------------

# B8 consumes MandateSnapshot and ShoppingRequest from B7's existing models.
# They are imported in dependent modules; not redefined here to avoid duplication.
