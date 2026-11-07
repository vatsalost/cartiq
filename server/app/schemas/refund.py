"""Refund schemas for PayPal order transactions."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class RefundRequest(BaseModel):
    """Refund request payload. Client cannot specify amount."""

    reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Reason for requesting refund",
    )


class RefundResponse(BaseModel):
    """Result of confirmed PayPal full refund operation."""

    refund_id: uuid.UUID
    order_id: uuid.UUID
    paypal_refund_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
