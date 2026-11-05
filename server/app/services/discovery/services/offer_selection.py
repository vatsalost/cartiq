"""Deterministic offer selection service enforcing user mandates and constraints."""

from decimal import Decimal
import logging
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from server.app.services.discovery.constants import OfferAvailability
from server.app.services.discovery.exceptions import (
    CurrencyMismatchError,
    MandateConstraintViolationError,
    OfferNotFoundError,
    OfferUnavailableError,
)
from server.app.services.discovery.models.offer import NormalizedOffer
from server.app.services.discovery.models.product import NormalizedProduct

logger = logging.getLogger("cartiq.channel3.selection")


class SpendingMandate(BaseModel):
    """Read-only user financial mandate constraints passed into offer selection."""

    model_config = ConfigDict(extra="ignore")

    max_budget: Optional[Decimal] = Field(
        default=None,
        description="Overall spending limit across the cart/proposal."
    )
    per_item_cap: Optional[Decimal] = Field(
        default=None,
        description="Maximum ceiling price permitted for a single item."
    )
    currency: str = Field(
        default="USD",
        description="Expected ISO 4217 currency code for the purchase."
    )
    allowed_domains: Optional[list[str]] = Field(
        default=None,
        description="Whitelisted merchant domains. If specified, offer domain must be in this list."
    )
    blocked_domains: Optional[list[str]] = Field(
        default=None,
        description="Blacklisted merchant domains. If specified, offer domain must NOT be in this list."
    )


class OfferSelectionService:
    """Deterministic selection service that validates candidates against hard constraints.

    LLM choices are strictly advisory. The Python engine validates whether the offer
    exists, is in stock, matches currency, and adheres to the user's spending mandate.
    """

    @staticmethod
    def select_offer(
        product: NormalizedProduct,
        offer_key: str,
        mandate: Optional[SpendingMandate] = None,
    ) -> NormalizedOffer:
        """Select and deterministically validate a specific retailer offer against mandates.

        Args:
            product: The canonical NormalizedProduct containing retailer candidate offers.
            offer_key: The exact deterministic key of the target offer.
            mandate: Read-only spending limits and merchant policies.

        Returns:
            The verified NormalizedOffer.

        Raises:
            OfferNotFoundError: If offer_key does not exist on the product.
            OfferUnavailableError: If offer is out of stock.
            CurrencyMismatchError: If offer currency does not match mandate.
            MandateConstraintViolationError: If offer exceeds price cap or violates domain policy.
        """
        # 1. Locate requested offer
        offer = product.get_offer(offer_key)
        if not offer:
            logger.warning("Offer key '%s' not found on product '%s'", offer_key, product.product_id)
            raise OfferNotFoundError(offer_key=offer_key, product_id=product.product_id)

        # 2. Reject unavailable offers
        if offer.availability != OfferAvailability.IN_STOCK.value:
            logger.warning("Offer '%s' is unavailable (status=%s)", offer_key, offer.availability)
            raise OfferUnavailableError(offer_key=offer_key, reason=f"Status is {offer.availability}")

        # 3. Mandate constraint checks (if mandate is supplied)
        if mandate:
            # Currency compatibility
            if mandate.currency and offer.currency.upper() != mandate.currency.upper():
                logger.warning(
                    "Offer currency '%s' does not match mandate currency '%s'",
                    offer.currency,
                    mandate.currency,
                )
                raise CurrencyMismatchError(
                    offer_currency=offer.currency,
                    expected_currency=mandate.currency,
                )

            # Per-item cap check
            if mandate.per_item_cap is not None and offer.price_amount > mandate.per_item_cap:
                msg = (
                    f"Offer price {offer.price_amount} {offer.currency} exceeds "
                    f"per-item cap of {mandate.per_item_cap} {mandate.currency}."
                )
                logger.warning(msg)
                raise MandateConstraintViolationError(msg)

            # Max total budget check
            if mandate.max_budget is not None and offer.price_amount > mandate.max_budget:
                msg = (
                    f"Offer price {offer.price_amount} {offer.currency} exceeds "
                    f"total maximum budget of {mandate.max_budget} {mandate.currency}."
                )
                logger.warning(msg)
                raise MandateConstraintViolationError(msg)

            # Domain whitelist check
            domain_norm = offer.domain.lower().removeprefix("www.")
            if mandate.allowed_domains:
                allowed_norm = {d.lower().removeprefix("www.") for d in mandate.allowed_domains}
                if domain_norm not in allowed_norm:
                    msg = f"Retailer domain '{offer.domain}' is not in allowed domain whitelist."
                    logger.warning(msg)
                    raise MandateConstraintViolationError(msg)

            # Domain blacklist check
            if mandate.blocked_domains:
                blocked_norm = {d.lower().removeprefix("www.") for d in mandate.blocked_domains}
                if domain_norm in blocked_norm:
                    msg = f"Retailer domain '{offer.domain}' is prohibited by domain blacklist."
                    logger.warning(msg)
                    raise MandateConstraintViolationError(msg)

        logger.info("Offer '%s' from '%s' successfully selected and validated", offer_key, offer.domain)
        return offer
