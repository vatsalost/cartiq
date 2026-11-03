"""Shopping request schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequestFilters(BaseModel):
    """Optional structured filters provided alongside natural language text."""

    category: Optional[str] = Field(None, max_length=100)
    max_price: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    currency: Optional[str] = Field("USD", min_length=3, max_length=3)
    preferred_brand: Optional[str] = Field(None, max_length=100)
    preferred_retailer: Optional[str] = Field(None, max_length=100)


class RequestCreate(BaseModel):
    """Payload to initiate a natural language shopping request."""

    text: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language description of desired product",
    )
    filters: Optional[RequestFilters] = Field(
        default=None,
        description="Optional structured constraints",
    )

    @field_validator("text")
    @classmethod
    def validate_non_whitespace_text(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 3:
            raise ValueError("Request text must contain at least 3 non-whitespace characters.")
        return clean


class RequestCreateResponse(BaseModel):
    """HTTP 202 Accepted response for shopping request submission."""

    request_id: uuid.UUID
    status: str = "queued"
    stream_url: str


class RequestDetailResponse(BaseModel):
    """Detailed status of a shopping request."""

    id: uuid.UUID
    user_id: uuid.UUID
    mandate_id: uuid.UUID
    mandate_version: int
    request_text: str
    normalized_intent: Optional[Dict[str, Any]] = None
    status: str
    error_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestCancelResponse(BaseModel):
    """Result of request cancellation."""

    request_id: uuid.UUID
    status: str
    message: str
    cancelled_at: datetime


class RequestEventResponse(BaseModel):
    """Progress event sent through SSE."""

    id: int
    request_id: uuid.UUID
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
