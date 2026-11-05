"""Structured exceptions for the Channel3 B6 module.

All exceptions prevent credential and secret leakage by redacting sensitive data
before message formatting.
"""

from typing import Optional


def _redact_secrets(message: str, secrets: Optional[list[str]] = None) -> str:
    """Safely redact any sensitive token or API key from error messages."""
    if not secrets:
        return message
    redacted = message
    for secret in secrets:
        if secret and len(secret) > 4:
            redacted = redacted.replace(secret, f"{secret[:3]}***[REDACTED]")
    return redacted


class Channel3Error(Exception):
    """Base exception for all Channel3 module errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, safe_code: str = "CHANNEL3_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.safe_code = safe_code

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.safe_code}, status={self.status_code}, message={self.message!r})"


class Channel3AuthError(Channel3Error):
    """Authentication or authorization failure with Channel3 API."""

    def __init__(self, message: str = "Authentication failed: invalid or missing Channel3 API key.", status_code: int = 401):
        super().__init__(message=message, status_code=status_code, safe_code="AUTH_FAILURE")


class Channel3BadRequestError(Channel3Error):
    """Invalid request payload or malformed query."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message=message, status_code=status_code, safe_code="BAD_REQUEST")


class Channel3NotFoundError(Channel3Error):
    """Product, offer, or requested resource not found in Channel3 catalog."""

    def __init__(self, message: str = "Requested resource was not found.", status_code: int = 404):
        super().__init__(message=message, status_code=status_code, safe_code="NOT_FOUND")


class Channel3RateLimitError(Channel3Error):
    """Channel3 API rate limit exceeded (HTTP 429)."""

    def __init__(self, message: str = "Channel3 rate limit exceeded.", retry_after: Optional[float] = None):
        super().__init__(message=message, status_code=429, safe_code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class Channel3ServerError(Channel3Error):
    """Channel3 5xx internal server error."""

    def __init__(self, message: str = "Channel3 upstream service encountered an internal error.", status_code: int = 500):
        super().__init__(message=message, status_code=status_code, safe_code="SERVER_ERROR")


class Channel3NetworkError(Channel3Error):
    """Network connection, DNS resolution, or transport failure."""

    def __init__(self, message: str = "Failed to establish network connection to Channel3 API."):
        super().__init__(message=message, status_code=None, safe_code="NETWORK_ERROR")


class Channel3TimeoutError(Channel3Error):
    """Request timeout when connecting to or reading from Channel3 API."""

    def __init__(self, message: str = "Channel3 API request timed out."):
        super().__init__(message=message, status_code=None, safe_code="TIMEOUT")


class Channel3ValidationError(Channel3Error):
    """Channel3 response payload structure validation failure."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=None, safe_code="VALIDATION_ERROR")


class OfferNotFoundError(Channel3Error):
    """Requested offer key does not exist on the product."""

    def __init__(self, offer_key: str, product_id: str):
        message = f"Offer '{offer_key}' does not exist on product '{product_id}'."
        super().__init__(message=message, status_code=None, safe_code="OFFER_NOT_FOUND")
        self.offer_key = offer_key
        self.product_id = product_id


class OfferUnavailableError(Channel3Error):
    """Requested offer is out of stock or unavailable."""

    def __init__(self, offer_key: str, reason: str = "Offer is out of stock"):
        message = f"Offer '{offer_key}' is unavailable: {reason}."
        super().__init__(message=message, status_code=None, safe_code="OFFER_UNAVAILABLE")
        self.offer_key = offer_key


class CurrencyMismatchError(Channel3Error):
    """Offer currency does not match requested or mandate currency."""

    def __init__(self, offer_currency: str, expected_currency: str):
        message = f"Offer currency '{offer_currency}' does not match expected '{expected_currency}'."
        super().__init__(message=message, status_code=None, safe_code="CURRENCY_MISMATCH")
        self.offer_currency = offer_currency
        self.expected_currency = expected_currency


class MandateConstraintViolationError(Channel3Error):
    """Selected offer violates spending mandate limits."""

    def __init__(self, reason: str):
        message = f"Mandate constraint violated: {reason}"
        super().__init__(message=message, status_code=None, safe_code="MANDATE_VIOLATION")
        self.reason = reason


class InvalidURLError(Channel3Error):
    """Retailer URL provided for lookup is invalid, malformed, or unsafe."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=None, safe_code="INVALID_URL")
