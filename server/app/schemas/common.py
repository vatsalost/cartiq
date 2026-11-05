"""Common schemas, error types, and pagination models."""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error object in Carti error envelope."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation of error")
    retryable: bool = Field(False, description="Whether the request may be retried")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context or validation details")


class ErrorEnvelope(BaseModel):
    """Standard Carti error response envelope."""

    error: ErrorDetail


class PaginationParams(BaseModel):
    """Standard pagination query parameters."""

    limit: int = Field(20, ge=1, le=100, description="Items per page")
    offset: int = Field(0, ge=0, description="Items to skip")


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""

    items: List[T]
    total: int
    limit: int
    offset: int
