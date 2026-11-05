"""Normalized product variant data model."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NormalizedVariant(BaseModel):
    """Represents a specific variant of a canonical product."""

    model_config = ConfigDict(extra="ignore")

    variant_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the variant if provided by Channel3."
    )
    name: Optional[str] = Field(
        default=None,
        description="Display name or descriptor of the variant."
    )
    options: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value mapping of variant options (e.g. {'Color': 'Blue', 'Size': 'M'})."
    )
    sku: Optional[str] = Field(
        default=None,
        description="Stock keeping unit identifier if available."
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Variant-specific product image URL if available."
    )
