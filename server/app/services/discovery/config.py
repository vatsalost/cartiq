"""Configuration settings for Channel3 client and services.

Safely handles API keys, timeouts, retry parameters, and default locale options.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, SecretStr, field_validator
from server.app.services.discovery.constants import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MIN_LIMIT,
    DEFAULT_COUNTRY,
    DEFAULT_LANGUAGE,
    DEFAULT_CURRENCY,
)


class Channel3Config(BaseModel):
    """Configuration container for Channel3 B6 Module."""

    api_key: Optional[SecretStr] = Field(
        default=None,
        description="Channel3 Server-side API key. Read from param or CHANNEL3_API_KEY environment variable."
    )
    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        description="Base URL for the Channel3 REST API."
    )
    timeout_seconds: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        gt=0.0,
        description="Read timeout for HTTP requests in seconds."
    )
    connect_timeout_seconds: float = Field(
        default=DEFAULT_CONNECT_TIMEOUT_SECONDS,
        gt=0.0,
        description="Connection timeout for HTTP requests in seconds."
    )
    max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        ge=0,
        le=10,
        description="Maximum retry attempts on transient network or rate-limit errors."
    )
    backoff_factor: float = Field(
        default=DEFAULT_BACKOFF_FACTOR,
        ge=0.0,
        description="Exponential backoff multiplier for retries."
    )
    default_limit: int = Field(
        default=DEFAULT_LIMIT,
        ge=MIN_LIMIT,
        le=MAX_LIMIT,
        description="Default number of search items to request."
    )
    max_limit: int = Field(
        default=MAX_LIMIT,
        ge=MIN_LIMIT,
        description="Hard maximum limit allowed per search query."
    )
    default_country: str = Field(
        default=DEFAULT_COUNTRY,
        description="Default 2-letter ISO country code."
    )
    default_language: str = Field(
        default=DEFAULT_LANGUAGE,
        description="Default 2-letter ISO language code."
    )
    default_currency: str = Field(
        default=DEFAULT_CURRENCY,
        description="Default ISO 4217 currency code."
    )

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_api_key(cls, v: Optional[object]) -> Optional[SecretStr]:
        if v is None:
            return None
        if isinstance(v, str):
            return SecretStr(v) if v.strip() else None
        if isinstance(v, SecretStr):
            return v
        return None

    def get_api_key_value(self) -> Optional[str]:
        """Return the unwrapped secret string value safely."""
        return self.api_key.get_secret_value() if self.api_key else None

    def __repr__(self) -> str:
        masked_key = "***" if self.api_key else "None"
        return (
            f"Channel3Config(base_url={self.base_url!r}, api_key={masked_key!r}, "
            f"timeout={self.timeout_seconds}, retries={self.max_retries})"
        )

    def __str__(self) -> str:
        return self.__repr__()
