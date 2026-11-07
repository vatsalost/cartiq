"""Validators for raw Channel3 API responses and entities."""

from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from server.app.services.discovery.constants import OfferAvailability, OfferCondition
from server.app.services.discovery.exceptions import Channel3ValidationError


class ResponseValidator:
    """Validates raw and parsed data structures from Channel3."""

    @staticmethod
    def validate_product_id(product_id: Any) -> str:
        """Ensure product ID is a valid non-empty string."""
        if not product_id or not isinstance(product_id, (str, int)):
            raise Channel3ValidationError(f"Invalid product ID: {product_id!r}")
        clean_id = str(product_id).strip()
        if not clean_id:
            raise Channel3ValidationError("Product ID cannot be blank.")
        return clean_id

    @staticmethod
    def validate_title(title: Any) -> str:
        """Ensure product title is a non-empty string."""
        if not title or not isinstance(title, str):
            raise Channel3ValidationError(f"Invalid product title: {title!r}")
        clean = title.strip()
        if not clean:
            raise Channel3ValidationError("Product title cannot be empty.")
        return clean

    @staticmethod
    def validate_price(price_val: Any) -> Decimal:
        """Validate and parse a monetary amount to Decimal.

        Rejects negative or non-numeric prices.
        """
        if price_val is None:
            raise Channel3ValidationError("Offer price cannot be None.")
        try:
            d = Decimal(str(price_val).strip())
        except (InvalidOperation, ValueError, TypeError) as e:
            raise Channel3ValidationError(f"Invalid price amount '{price_val}': {e}") from e

        if d < Decimal("0.00"):
            raise Channel3ValidationError(f"Price cannot be negative: {d}")
        return d

    @staticmethod
    def validate_currency(currency_val: Any) -> str:
        """Validate currency code is an ISO 4217 3-letter code."""
        if not currency_val or not isinstance(currency_val, str):
            raise Channel3ValidationError(f"Invalid currency code: {currency_val!r}")
        clean = currency_val.strip().upper()
        if len(clean) != 3 or not clean.isalpha():
            raise Channel3ValidationError(f"Currency must be a 3-letter ISO code: {currency_val!r}")
        return clean

    @staticmethod
    def validate_domain(domain_val: Any, buy_url: Optional[str] = None) -> str:
        """Ensure domain is non-empty and well-formed."""
        if not domain_val or not isinstance(domain_val, str):
            if buy_url and isinstance(buy_url, str):
                from urllib.parse import urlparse
                parsed = urlparse(buy_url)
                if parsed.hostname:
                    return parsed.hostname.lower().removeprefix("www.")
            raise Channel3ValidationError(f"Invalid retailer domain: {domain_val!r}")
        clean = domain_val.strip().lower()
        if clean.startswith("http://"):
            clean = clean[7:]
        elif clean.startswith("https://"):
            clean = clean[8:]
        clean = clean.removeprefix("www.").split("/")[0].split(":")[0]
        if not clean:
            raise Channel3ValidationError("Retailer domain cannot be empty.")
        return clean

    @staticmethod
    def normalize_availability(status_val: Any) -> str:
        """Map raw availability strings to standardized OfferAvailability."""
        if not status_val or not isinstance(status_val, str):
            return OfferAvailability.UNKNOWN.value

        raw = status_val.strip().lower().replace("_", "").replace("-", "").replace(" ", "")
        if raw in ("instock", "available", "true", "in_stock"):
            return OfferAvailability.IN_STOCK.value
        elif raw in ("outofstock", "unavailable", "soldout", "false", "out_of_stock"):
            return OfferAvailability.OUT_OF_STOCK.value
        return OfferAvailability.UNKNOWN.value

    @staticmethod
    def normalize_condition(cond_val: Any) -> str:
        """Map raw condition strings to standardized OfferCondition."""
        if not cond_val or not isinstance(cond_val, str):
            return OfferCondition.UNKNOWN.value

        raw = cond_val.strip().lower()
        if "new" in raw:
            return OfferCondition.NEW.value
        elif "refurb" in raw:
            return OfferCondition.REFURBISHED.value
        elif "used" in raw or "preowned" in raw:
            return OfferCondition.USED.value
        return OfferCondition.UNKNOWN.value
