"""Product detail retrieval and freshness verification service."""

from decimal import Decimal
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field
from server.app.services.discovery.client.channel3_client import Channel3Client
from server.app.services.discovery.constants import OfferAvailability, RefreshStatus
from server.app.services.discovery.models.locale import Channel3Locale
from server.app.services.discovery.models.offer import NormalizedOffer
from server.app.services.discovery.models.product import NormalizedProduct

logger = logging.getLogger("cartiq.channel3.product")


class ProductRefreshResult(BaseModel):
    """Structured result of refreshing product offers prior to proposal and payment capture."""

    product: NormalizedProduct = Field(
        description="Fresh canonical product returned by Channel3."
    )
    selected_offer: Optional[NormalizedOffer] = Field(
        default=None,
        description="Fresh normalized offer corresponding to the selected offer_key."
    )
    status: RefreshStatus = Field(
        description="Evaluation result comparing fresh data against baseline."
    )
    old_price: Optional[Decimal] = Field(
        default=None,
        description="Baseline price before refresh."
    )
    new_price: Optional[Decimal] = Field(
        default=None,
        description="Fresh price returned by provider."
    )
    old_availability: Optional[str] = Field(
        default=None,
        description="Baseline availability before refresh."
    )
    new_availability: Optional[str] = Field(
        default=None,
        description="Fresh availability returned by provider."
    )
    details: str = Field(
        description="Deterministic human and machine-readable explanation of freshness check."
    )

    @property
    def is_safe_for_checkout(self) -> bool:
        """Determines if the refreshed offer is stable and available for purchase."""
        return (
            self.status == RefreshStatus.UNCHANGED
            and self.selected_offer is not None
            and self.selected_offer.availability == OfferAvailability.IN_STOCK.value
        )


class ProductService:
    """Service for canonical product lookup and strict pre-checkout price re-validation."""

    def __init__(self, client: Channel3Client):
        self.client = client

    async def get_product_details(
        self,
        product_id: str,
        locale: Optional[Channel3Locale] = None,
        variant_options: Optional[dict[str, str]] = None,
    ) -> NormalizedProduct:
        """Retrieve canonical product details and current multi-retailer offers."""
        logger.info("Retrieving product details for ID: %s", product_id)
        return await self.client.get_product(
            product_id=product_id,
            locale=locale,
            variant_options=variant_options,
        )

    async def refresh_product(
        self,
        product_id: str,
        selected_offer_key: str,
        baseline_offer: Optional[NormalizedOffer] = None,
        locale: Optional[Channel3Locale] = None,
        variant_options: Optional[dict[str, str]] = None,
    ) -> ProductRefreshResult:
        """Freshly re-fetch product details and evaluate offer stability before proposal creation or payment.

        Never silently substitutes a missing or modified offer with another retailer.

        Args:
            product_id: Canonical Channel3 product identifier.
            selected_offer_key: Exact stable key of the offer originally selected.
            baseline_offer: Previous observation of the offer to compare against.
            locale: Optional regional/currency configuration.
            variant_options: Optional variant selections.

        Returns:
            ProductRefreshResult describing price, availability, or existence shifts.
        """
        logger.info("Executing mandatory freshness re-validation for product %s, offer %s", product_id, selected_offer_key)

        fresh_product = await self.client.get_product(
            product_id=product_id,
            locale=locale,
            variant_options=variant_options,
        )

        fresh_offer = fresh_product.get_offer(selected_offer_key)

        # 1. Offer completely disappeared from retailer catalog
        if fresh_offer is None:
            return ProductRefreshResult(
                product=fresh_product,
                selected_offer=None,
                status=RefreshStatus.OFFER_DISAPPEARED,
                old_price=baseline_offer.price_amount if baseline_offer else None,
                new_price=None,
                old_availability=baseline_offer.availability if baseline_offer else None,
                new_availability=None,
                details=f"Selected offer '{selected_offer_key}' is no longer available from the retailer.",
            )

        # If no baseline was passed, evaluate fresh offer state in isolation
        if baseline_offer is None:
            if fresh_offer.availability != OfferAvailability.IN_STOCK.value:
                return ProductRefreshResult(
                    product=fresh_product,
                    selected_offer=fresh_offer,
                    status=RefreshStatus.AVAILABILITY_CHANGED,
                    old_price=None,
                    new_price=fresh_offer.price_amount,
                    old_availability=None,
                    new_availability=fresh_offer.availability,
                    details=f"Offer is not in stock (current status: {fresh_offer.availability}).",
                )
            return ProductRefreshResult(
                product=fresh_product,
                selected_offer=fresh_offer,
                status=RefreshStatus.UNCHANGED,
                old_price=fresh_offer.price_amount,
                new_price=fresh_offer.price_amount,
                old_availability=fresh_offer.availability,
                new_availability=fresh_offer.availability,
                details="Fresh offer verified in stock.",
            )

        # 2. Compare against baseline offer
        old_price = baseline_offer.price_amount
        new_price = fresh_offer.price_amount
        old_avail = baseline_offer.availability
        new_avail = fresh_offer.availability

        # Check currency shift
        if fresh_offer.currency.upper() != baseline_offer.currency.upper():
            return ProductRefreshResult(
                product=fresh_product,
                selected_offer=fresh_offer,
                status=RefreshStatus.CURRENCY_CHANGED,
                old_price=old_price,
                new_price=new_price,
                old_availability=old_avail,
                new_availability=new_avail,
                details=f"Currency changed from {baseline_offer.currency} to {fresh_offer.currency}.",
            )

        # Check domain/retailer shift
        if fresh_offer.domain != baseline_offer.domain:
            return ProductRefreshResult(
                product=fresh_product,
                selected_offer=fresh_offer,
                status=RefreshStatus.RETAILER_CHANGED,
                old_price=old_price,
                new_price=new_price,
                old_availability=old_avail,
                new_availability=new_avail,
                details=f"Retailer changed from '{baseline_offer.domain}' to '{fresh_offer.domain}'.",
            )

        # Check availability shift
        if new_avail != old_avail or new_avail != OfferAvailability.IN_STOCK.value:
            return ProductRefreshResult(
                product=fresh_product,
                selected_offer=fresh_offer,
                status=RefreshStatus.AVAILABILITY_CHANGED,
                old_price=old_price,
                new_price=new_price,
                old_availability=old_avail,
                new_availability=new_avail,
                details=f"Availability shifted from '{old_avail}' to '{new_avail}'.",
            )

        # Check price shift
        if new_price != old_price:
            return ProductRefreshResult(
                product=fresh_product,
                selected_offer=fresh_offer,
                status=RefreshStatus.PRICE_CHANGED,
                old_price=old_price,
                new_price=new_price,
                old_availability=old_avail,
                new_availability=new_avail,
                details=f"Price changed from {old_price} to {new_price} {fresh_offer.currency}.",
            )

        # Everything matches and is in stock
        return ProductRefreshResult(
            product=fresh_product,
            selected_offer=fresh_offer,
            status=RefreshStatus.UNCHANGED,
            old_price=old_price,
            new_price=new_price,
            old_availability=old_avail,
            new_availability=new_avail,
            details="Offer is verified fresh and identical to baseline.",
        )
