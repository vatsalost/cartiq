"""Configuration parameters and scoring weights for candidate ranking."""

from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class ScoringWeights(BaseModel):
    """Configurable weights for deterministic candidate scoring.

    All weights must be non-negative.
    """

    price_weight: float = Field(
        default=0.35,
        ge=0.0,
        description="Weight given to price relative to budget/cap."
    )
    preferred_attributes_weight: float = Field(
        default=0.25,
        ge=0.0,
        description="Weight given to matching optional user-preferred attributes."
    )
    preferred_brands_weight: float = Field(
        default=0.15,
        ge=0.0,
        description="Weight given to matching user-specified preferred brands."
    )
    preferred_retailers_weight: float = Field(
        default=0.15,
        ge=0.0,
        description="Weight given to matching user-specified preferred retailer domains."
    )
    condition_weight: float = Field(
        default=0.05,
        ge=0.0,
        description="Weight given to matching target product condition."
    )
    data_quality_weight: float = Field(
        default=0.05,
        ge=0.0,
        description="Weight given to data completeness (images, descriptions)."
    )

    @model_validator(mode="after")
    def validate_total_weight(self) -> "ScoringWeights":
        total = (
            self.price_weight
            + self.preferred_attributes_weight
            + self.preferred_brands_weight
            + self.preferred_retailers_weight
            + self.condition_weight
            + self.data_quality_weight
        )
        if total <= 0.0:
            raise ValueError("Sum of scoring weights must be greater than 0.")
        return self


class RankingConfig(BaseModel):
    """Configuration container for candidate ranking and explanation service."""

    weights: ScoringWeights = Field(
        default_factory=ScoringWeights,
        description="Scoring factor weights."
    )
    max_data_age_seconds: int = Field(
        default=86400,  # 24 hours
        ge=60,
        description="Maximum allowed age of offer data in seconds before considered stale."
    )
    min_price_epsilon: Decimal = Field(
        default=Decimal("0.01"),
        gt=Decimal("0.00"),
        description="Minimum monetary increment used for price comparisons."
    )
    enable_llm_explanation: bool = Field(
        default=False,
        description="Whether to use optional LLM explanation adapter when available."
    )
    max_explanation_length: int = Field(
        default=500,
        gt=50,
        description="Maximum character length of generated explanation."
    )
