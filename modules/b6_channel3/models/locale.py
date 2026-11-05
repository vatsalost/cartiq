"""Locale specification model for Channel3 queries."""

from typing import Any
from pydantic import BaseModel, Field, field_validator
from modules.b6_channel3.constants import (
    DEFAULT_COUNTRY,
    DEFAULT_LANGUAGE,
    DEFAULT_CURRENCY,
)


class Channel3Locale(BaseModel):
    """Encapsulates regional, linguistic, and monetary settings for Channel3."""

    country: str = Field(
        default=DEFAULT_COUNTRY,
        description="2-letter ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'CA')."
    )
    language: str = Field(
        default=DEFAULT_LANGUAGE,
        description="2-letter ISO 639-1 language code (e.g., 'en', 'es', 'fr')."
    )
    currency: str = Field(
        default=DEFAULT_CURRENCY,
        description="3-letter ISO 4217 currency code (e.g., 'USD', 'EUR', 'GBP')."
    )

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        code = v.strip().upper()
        if len(code) != 2 or not code.isalpha():
            raise ValueError(f"Country code must be a 2-letter ISO code, got: {v!r}")
        return code

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        code = v.strip().lower()
        if len(code) != 2 or not code.isalpha():
            raise ValueError(f"Language code must be a 2-letter ISO code, got: {v!r}")
        return code

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        code = v.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError(f"Currency code must be a 3-letter ISO code, got: {v!r}")
        return code

    def to_dict(self) -> dict[str, str]:
        """Return locale parameters as a dictionary."""
        return {
            "country": self.country,
            "language": self.language,
            "currency": self.currency,
        }
