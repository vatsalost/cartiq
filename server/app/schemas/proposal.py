"""Proposal schemas and checkout order initiation schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class GuardrailRuleResult(BaseModel):
    """Result of an individual deterministic guardrail check."""

    rule: str
    passed: bool
    actual: Optional[str] = None
    limit: Optional[str] = None
    reason: str


class ProposalProductSummary(BaseModel):
    """Summary snapshot of the proposed product."""

    product_id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProposalOfferSummary(BaseModel):
    """Summary snapshot of the selected retailer offer."""

    offer_id: uuid.UUID
    domain: str
    buy_url: str
    price_amount: Decimal
    currency: str
    availability: str
    condition: str


class ProposalResponse(BaseModel):
    """Complete proposal review representation."""

    id: uuid.UUID
    request_id: uuid.UUID
    user_id: uuid.UUID
    mandate_id: uuid.UUID
    mandate_version: int
    candidate_id: uuid.UUID
    offer_id: uuid.UUID
    quantity: int
    unit_price_at_proposal: Decimal
    subtotal_at_proposal: Decimal
    currency: str
    rationale: str
    guardrail_result: Dict[str, Any]
    verification_result: Optional[Dict[str, Any]] = None
    status: str
    expires_at: datetime
    created_at: datetime

    # Embedded snapshots for frontend convenience
    product: Optional[ProposalProductSummary] = None
    offer: Optional[ProposalOfferSummary] = None

    model_config = ConfigDict(from_attributes=True)


class ProposalCreateOrderRequest(BaseModel):
    """
    Request to initialize a PayPal order for an approved proposal.
    Note: Client NEVER passes amount, price, or currency!
    """

    checkout_attempt_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Client-side idempotency/attempt identifier",
    )


class ProposalCreateOrderResponse(BaseModel):
    """Response returning the created internal and PayPal order IDs."""

    order_id: uuid.UUID
    paypal_order_id: str
    status: str
    amount: Decimal
    currency: str
