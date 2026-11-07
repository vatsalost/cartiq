"""Normalized canonical product model."""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from server.app.services.discovery.constants import PROVIDER_NAME
from server.app.services.discovery.models.offer import NormalizedOffer
from server.app.services.discovery.models.variant import NormalizedVariant


class NormalizedProduct(BaseModel):
    """Internal canonical product representation for CartiQ.

    Separates product-level metadata from specific retailer offers.
    """

    model_config = ConfigDict(extra="ignore")

    provider: str = Field(
        default=PROVIDER_NAME,
        description="Data provider identifier (always 'channel3')."
    )
    product_id: str = Field(
        description="Canonical Channel3 product identifier."
    )
    title: str = Field(
        description="Normalized product display title."
    )
    brand: Optional[str] = Field(
        default=None,
        description="Brand or manufacturer name."
    )
    category: Optional[str] = Field(
        default=None,
        description="Product catalog category or category taxonomy string."
    )
    description: Optional[str] = Field(
        default=None,
        description="Catalog description or marketing summary."
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Primary display image URL."
    )
    images: list[str] = Field(
        default_factory=list,
        description="List of all associated image URLs."
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized technical attributes, specifications, and key features."
    )
    variants: list[NormalizedVariant] = Field(
        default_factory=list,
        description="Product variants (colors, sizes, configurations)."
    )
    offers: list[NormalizedOffer] = Field(
        default_factory=list,
        description="List of retailer offers currently available for this product."
    )
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when product was fetched or refreshed."
    )

    def get_offer(self, offer_key: str) -> Optional[NormalizedOffer]:
        """Locate an offer by its exact deterministic key."""
        for offer in self.offers:
            if offer.offer_key == offer_key:
                return offer
        return None

    def get_best_price_offer(self, currency: Optional[str] = None) -> Optional[NormalizedOffer]:
        """Find the lowest-priced available in-stock offer, optionally filtered by currency."""
        matching = [
            o for o in self.offers
            if o.availability.lower() == "instock"
            and (currency is None or o.currency.upper() == currency.upper())
        ]
        if not matching:
            return None
        return min(matching, key=lambda o: o.price_amount)
