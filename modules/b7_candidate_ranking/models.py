"""Data models for candidate ranking, eligibility evaluation, and explanations."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RejectionCode(StrEnum):
    """Specific, non-generic rejection codes for excluded candidate options."""
    OUT_OF_STOCK = "OUT_OF_STOCK"
    WRONG_CURRENCY = "WRONG_CURRENCY"
    ABOVE_REQUEST_PRICE_LIMIT = "ABOVE_REQUEST_PRICE_LIMIT"
    ABOVE_PER_ITEM_CAP = "ABOVE_PER_ITEM_CAP"
    BLOCKED_CATEGORY = "BLOCKED_CATEGORY"
    CATEGORY_NOT_ALLOWED = "CATEGORY_NOT_ALLOWED"
    RETAILER_NOT_ALLOWED = "RETAILER_NOT_ALLOWED"
    WRONG_CONDITION = "WRONG_CONDITION"
    MISSING_REQUIRED_ATTRIBUTE = "MISSING_REQUIRED_ATTRIBUTE"
    INSUFFICIENT_PRODUCT_DATA = "INSUFFICIENT_PRODUCT_DATA"
    STALE_PRODUCT_DATA = "STALE_PRODUCT_DATA"
    INVALID_OFFER_DATA = "INVALID_OFFER_DATA"


class EligibilityStatus(StrEnum):
    """Eligibility status of a candidate offer."""
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class RejectionDetail(BaseModel):
    """Structured record of a single concrete rejection reason."""

    model_config = ConfigDict(extra="ignore")

    code: RejectionCode = Field(
        description="Structured rejection category code."
    )
    reason: str = Field(
        description="Detailed, factual description of why the candidate failed."
    )


class ShoppingRequest(BaseModel):
    """Structured representation of the buyer's shopping intent and constraints."""

    model_config = ConfigDict(extra="ignore")

    original_text: str = Field(
        description="Original user request string in natural language."
    )
    category: Optional[str] = Field(
        default=None,
        description="Target product category requested."
    )
    required_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Mandatory key-value attributes (e.g. {'color': 'black', 'connectivity': 'bluetooth'})."
    )
    preferred_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional preferred key-value attributes."
    )
    max_price: Optional[Decimal] = Field(
        default=None,
        description="Maximum price the user is willing to spend."
    )
    currency: str = Field(
        default="USD",
        description="Expected 3-letter ISO 4217 currency code."
    )
    preferred_brands: list[str] = Field(
        default_factory=list,
        description="Explicit user-preferred brand names."
    )
    preferred_retailers: list[str] = Field(
        default_factory=list,
        description="Explicit user-preferred retailer domains."
    )
    required_condition: Optional[str] = Field(
        default=None,
        description="Target condition required by user (e.g. 'new', 'refurbished')."
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if len(clean) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code: {v!r}")
        return clean

    @field_validator("max_price", mode="before")
    @classmethod
    def parse_max_price(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class MandateSnapshot(BaseModel):
    """Immutable view of active financial and policy constraints enforced by the system."""

    model_config = ConfigDict(extra="ignore")

    total_budget: Optional[Decimal] = Field(
        default=None,
        description="Overall budget limit for the purchase session."
    )
    currency: str = Field(
        default="USD",
        description="Mandate ISO 4217 currency code."
    )
    per_item_cap: Optional[Decimal] = Field(
        default=None,
        description="Strict ceiling on any individual product offer."
    )
    allowed_categories: Optional[list[str]] = Field(
        default=None,
        description="Permitted categories. If defined, item must match one of these."
    )
    blocked_categories: Optional[list[str]] = Field(
        default=None,
        description="Prohibited categories. If matched, candidate is rejected."
    )
    allowed_retailers: Optional[list[str]] = Field(
        default=None,
        description="Whitelisted retailer domains."
    )
    max_quantity: Optional[int] = Field(
        default=None,
        description="Maximum allowed item quantity."
    )
    price_tolerance: Optional[Decimal] = Field(
        default=None,
        description="Allowable variance over base price."
    )
    status: str = Field(
        default="active",
        description="Mandate lifecycle state."
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiration timestamp of the mandate."
    )

    @field_validator("total_budget", "per_item_cap", "price_tolerance", mode="before")
    @classmethod
    def parse_decimals(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class CandidateOffer(BaseModel):
    """Single merchant offer evaluated in B7."""

    model_config = ConfigDict(extra="ignore")

    offer_key: str = Field(
        description="Deterministic unique offer identifier."
    )
    domain: str = Field(
        description="Retailer domain (e.g. 'target.com')."
    )
    buy_url: str = Field(
        description="Direct merchant or tracking link."
    )
    price_amount: Decimal = Field(
        description="Exact price amount in Decimal."
    )
    currency: str = Field(
        description="3-letter ISO currency code."
    )
    availability: str = Field(
        description="Availability status string (e.g. 'InStock', 'OutOfStock')."
    )
    condition: str = Field(
        default="new",
        description="Product condition (e.g. 'new', 'used', 'refurbished')."
    )
    variant_info: Optional[dict[str, Any]] = Field(
        default=None,
        description="Variant configuration data if applicable."
    )
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when offer was observed."
    )

    @field_validator("price_amount", mode="before")
    @classmethod
    def parse_price(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class CandidateProduct(BaseModel):
    """Canonical product candidate metadata."""

    model_config = ConfigDict(extra="ignore")

    product_id: str = Field(
        description="Canonical Channel3 product identifier."
    )
    title: str = Field(
        description="Product name or title."
    )
    brand: Optional[str] = Field(
        default=None,
        description="Brand manufacturer."
    )
    category: Optional[str] = Field(
        default=None,
        description="Product category taxonomy string."
    )
    description: Optional[str] = Field(
        default=None,
        description="Catalog description."
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Catalog key-value attributes."
    )
    variants: list[Any] = Field(
        default_factory=list,
        description="Product variants."
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Primary display image URL."
    )
    offers: list[CandidateOffer] = Field(
        default_factory=list,
        description="List of retailer offers available."
    )
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC observation timestamp."
    )


class CandidateOption(BaseModel):
    """Discrete pairing of a canonical product with a specific retailer offer."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: str = Field(
        description="Unique ID for this product+offer pairing."
    )
    product: CandidateProduct
    offer: CandidateOffer

    @classmethod
    def create(cls, product: CandidateProduct, offer: CandidateOffer) -> "CandidateOption":
        cand_id = f"{product.product_id}:{offer.offer_key}"
        return cls(candidate_id=cand_id, product=product, offer=offer)


class RankedCandidate(BaseModel):
    """Evaluated, scored, and ranked candidate option."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    product_id: str
    offer_key: str
    product_title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    domain: str
    price_amount: Decimal
    currency: str
    availability: str
    condition: str
    buy_url: str
    image_url: Optional[str] = None
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Product catalog key-value attributes.",
    )
    eligibility_status: EligibilityStatus
    ranking_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized ranking score between 0.0 and 1.0."
    )
    ranking_position: Optional[int] = Field(
        default=None,
        description="1-based ranking index among eligible candidates."
    )
    score_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Granular contribution of each scoring factor."
    )
    positive_matching_factors: list[str] = Field(
        default_factory=list,
        description="Fact-based reasons why this candidate performed well."
    )
    missing_or_uncertain_information: list[str] = Field(
        default_factory=list,
        description="Catalog fields that could not be verified."
    )
    rejection_reasons: list[RejectionDetail] = Field(
        default_factory=list,
        description="Specific rejection reasons if candidate is ineligible."
    )


class ComparisonResult(BaseModel):
    """Structured response of the Candidate Ranking and Explanation Service."""

    model_config = ConfigDict(extra="ignore")

    ranked_candidates: list[RankedCandidate] = Field(
        default_factory=list,
        description="Eligible candidates ordered by ranking score and tie-breakers."
    )
    rejected_candidates: list[RankedCandidate] = Field(
        default_factory=list,
        description="Candidates excluded during pre-filtering with concrete rejection details."
    )
    selected_candidate: Optional[RankedCandidate] = Field(
        default=None,
        description="The top-ranked eligible candidate option for concierge recommendation."
    )
    score_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Summary score breakdown of the selected candidate."
    )
    explanation: str = Field(
        description="Fact-grounded, concise explanation for the top recommendation and exclusions."
    )
    missing_or_uncertain_data: list[str] = Field(
        default_factory=list,
        description="Identified data gaps or unverified fields across candidates."
    )
    evaluation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when evaluation took place."
    )
