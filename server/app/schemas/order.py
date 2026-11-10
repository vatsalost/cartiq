"""Order and payment capture schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class OrderCaptureRequest(BaseModel):
    """
    Client capture notification after PayPal SDK onApprove callback.
    Client cannot specify amount or capture ID.
    """

    paypal_order_id: Optional[str] = Field(
        None,
        description="PayPal order ID received in onApprove callback for verification",
    )


class OrderCaptureResponse(BaseModel):
    """Result of server-side PayPal capture operation."""

    order_id: uuid.UUID
    id: Optional[uuid.UUID] = None
    paypal_order_id: str
    paypal_capture_id: str
    status: str
    amount: Decimal
    currency: str
    captured_at: datetime

    def model_post_init(self, __context: object) -> None:
        if self.id is None:
            self.id = self.order_id


class OrderRefundSummary(BaseModel):
    """Summary of refund if order was refunded."""

    refund_id: uuid.UUID
    paypal_refund_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailResponse(BaseModel):
    """Complete order receipt with payment status and retailer details."""

    id: uuid.UUID
    proposal_id: uuid.UUID
    user_id: uuid.UUID
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    budget_reserved: Decimal
    captured_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Product and retailer details from proposal
    product_title: Optional[str] = None
    retailer_domain: Optional[str] = None
    retailer_buy_url: Optional[str] = None
    quantity: int = 1

    # Demo note explaining fulfillment separation
    fulfillment_note: str = (
        "Sandbox payment completed to demo merchant. "
        "External retailer order was not automatically placed."
    )

    refunds: List[OrderRefundSummary] = []

    model_config = ConfigDict(from_attributes=True)


class OrderListItemResponse(BaseModel):
    """Summary row for order history view."""

    id: uuid.UUID
    proposal_id: uuid.UUID
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    product_title: Optional[str] = None
    retailer_domain: Optional[str] = None
    captured_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    items: List[OrderListItemResponse]
    total: int
    limit: int
    offset: int
