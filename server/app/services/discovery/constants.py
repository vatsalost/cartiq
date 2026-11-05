"""Constants for Channel3 integration module (B6).

Provides endpoint paths, status values, default timeouts, and configuration bounds.
"""

from enum import StrEnum

# Provider identification
PROVIDER_NAME = "channel3"

# Official Channel3 API endpoints
DEFAULT_BASE_URL = "https://api.trychannel3.com"
SEARCH_ENDPOINT = "/v1/search"
LOOKUP_ENDPOINT = "/v1/lookup"
PRODUCTS_ENDPOINT = "/v1/products"

# HTTP & Reliability Defaults
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_CONNECT_TIMEOUT_SECONDS = 5.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Pagination / Limits
DEFAULT_LIMIT = 20
MAX_LIMIT = 50
MIN_LIMIT = 1

# Default Locale
DEFAULT_COUNTRY = "US"
DEFAULT_LANGUAGE = "en"
DEFAULT_CURRENCY = "USD"


class OfferAvailability(StrEnum):
    """Normalized offer availability states."""
    IN_STOCK = "InStock"
    OUT_OF_STOCK = "OutOfStock"
    UNKNOWN = "Unknown"


class OfferCondition(StrEnum):
    """Normalized offer item condition."""
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    UNKNOWN = "unknown"


class RefreshStatus(StrEnum):
    """Product offer freshness evaluation status."""
    UNCHANGED = "UNCHANGED"
    PRICE_CHANGED = "PRICE_CHANGED"
    CURRENCY_CHANGED = "CURRENCY_CHANGED"
    AVAILABILITY_CHANGED = "AVAILABILITY_CHANGED"
    OFFER_DISAPPEARED = "OFFER_DISAPPEARED"
    RETAILER_CHANGED = "RETAILER_CHANGED"
    VARIANT_CHANGED = "VARIANT_CHANGED"
