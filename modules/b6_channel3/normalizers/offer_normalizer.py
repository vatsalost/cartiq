"""Normalizer for Channel3 retailer offers."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import Any, Optional, Union
from modules.b6_channel3.exceptions import Channel3ValidationError
from modules.b6_channel3.models.offer import NormalizedOffer
from modules.b6_channel3.validators.response_validator import ResponseValidator


class OfferNormalizer:
    """Parses and normalizes raw retailer offer structures into typed models."""

    @staticmethod
    def generate_offer_key(raw_offer: Union[dict[str, Any], NormalizedOffer]) -> str:
        """Generate a deterministic, stable offer identifier based on immutable listing attributes.

        Never relies on mutable price alone to ensure stability across price refreshes.
        """
        if isinstance(raw_offer, NormalizedOffer):
            return raw_offer.offer_key

        # If provider already supplies a stable offer identifier, use it
        explicit_id = raw_offer.get("offer_id") or raw_offer.get("id")
        if explicit_id:
            return f"ch3_offer_{explicit_id}"

        # Otherwise synthesize a stable SHA256 hash using merchant, domain, and canonical buy url
        domain = str(raw_offer.get("domain") or "").strip().lower()
        merchant_id = str(raw_offer.get("merchant_id") or "").strip()
        buy_url = str(raw_offer.get("url") or raw_offer.get("buy_url") or "").strip()

        # Clean URL query params that might be tracking/volatile if possible
        clean_url = buy_url.split("?")[0] if buy_url else ""

        key_material = f"{domain}:{merchant_id}:{clean_url}"
        digest = hashlib.sha256(key_material.encode("utf-8")).hexdigest()[:16]
        return f"off_{digest}"

    @classmethod
    def normalize_offer(
        cls,
        raw_offer: dict[str, Any],
        observed_at: Optional[datetime] = None,
    ) -> NormalizedOffer:
        """Normalize a single raw retailer offer dictionary.

        Args:
            raw_offer: Raw offer dict from Channel3.
            observed_at: Optional timestamp override.

        Returns:
            NormalizedOffer instance with exact Decimal price and validated attributes.

        Raises:
            Channel3ValidationError: If required offer fields are missing or invalid.
        """
        if not isinstance(raw_offer, dict):
            raise Channel3ValidationError(f"Expected offer dictionary, received: {type(raw_offer).__name__}")

        # Extract URL
        buy_url = raw_offer.get("url") or raw_offer.get("buy_url")
        if not buy_url or not isinstance(buy_url, str):
            raise Channel3ValidationError("Offer is missing a valid buy URL.")

        # Extract and validate domain
        raw_domain = raw_offer.get("domain")
        domain = ResponseValidator.validate_domain(raw_domain, buy_url=buy_url)

        # Extract price and currency: Channel3 may provide a price sub-object or direct keys
        raw_price_obj = raw_offer.get("price")
        price_val: Any = None
        currency_val: Any = None
        compare_at_val: Any = None

        if isinstance(raw_price_obj, dict):
            price_val = raw_price_obj.get("price")
            currency_val = raw_price_obj.get("currency")
            compare_at_val = raw_price_obj.get("compare_at_price")
        else:
            price_val = raw_price_obj if raw_price_obj is not None else raw_offer.get("price_amount")
            currency_val = raw_offer.get("currency")
            compare_at_val = raw_offer.get("compare_at_price")

        price_amount = ResponseValidator.validate_price(price_val)
        currency = ResponseValidator.validate_currency(currency_val)

        compare_at_price: Optional[Decimal] = None
        if compare_at_val is not None:
            try:
                compare_at_price = ResponseValidator.validate_price(compare_at_val)
            except Channel3ValidationError:
                compare_at_price = None

        commission_rate: Optional[Decimal] = None
        raw_comm = raw_offer.get("commission_rate")
        if raw_comm is not None:
            try:
                commission_rate = Decimal(str(raw_comm).strip())
            except Exception:
                commission_rate = None

        availability = ResponseValidator.normalize_availability(raw_offer.get("availability"))
        condition = ResponseValidator.normalize_condition(raw_offer.get("condition"))
        offer_key = cls.generate_offer_key(raw_offer)

        ts = observed_at or datetime.now(timezone.utc)

        return NormalizedOffer(
            offer_key=offer_key,
            domain=domain,
            price_amount=price_amount,
            currency=currency,
            availability=availability,
            condition=condition,
            buy_url=buy_url.strip(),
            observed_at=ts,
            merchant_id=str(raw_offer.get("merchant_id")) if raw_offer.get("merchant_id") else None,
            merchant_name=str(raw_offer.get("merchant_name")) if raw_offer.get("merchant_name") else None,
            compare_at_price=compare_at_price,
            commission_rate=commission_rate,
            extra_attributes={
                k: v for k, v in raw_offer.items()
                if k not in ("url", "buy_url", "domain", "price", "currency", "availability", "condition")
            },
        )

    @classmethod
    def normalize_offers(
        cls,
        raw_offers: list[dict[str, Any]],
        observed_at: Optional[datetime] = None,
    ) -> list[NormalizedOffer]:
        """Normalize a list of raw retailer offers, skipping completely malformed ones."""
        if not raw_offers or not isinstance(raw_offers, list):
            return []

        normalized: list[NormalizedOffer] = []
        for raw in raw_offers:
            if not isinstance(raw, dict):
                continue
            try:
                offer = cls.normalize_offer(raw, observed_at=observed_at)
                normalized.append(offer)
            except Channel3ValidationError:
                # Malformed individual offer is safely skipped rather than crashing the catalog
                continue
        return normalized
