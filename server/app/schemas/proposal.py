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
    mandate_version: int = 1
    candidate_id: uuid.UUID
    offer_id: uuid.UUID
    quantity: int = 1
    unit_price_at_proposal: Decimal
    subtotal_at_proposal: Decimal
    shipping_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Optional[Decimal] = None
    currency: str = "USD"
    rationale: str
    guardrail_result: Dict[str, Any]
    verification_result: Optional[Dict[str, Any]] = None
    verification_status: str = "unverified"
    product_snapshot: Optional[Dict[str, Any]] = None
    offer_snapshot: Optional[Dict[str, Any]] = None
    status: str
    expires_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Embedded snapshots for frontend convenience
    product: Optional[ProposalProductSummary] = None
    offer: Optional[ProposalOfferSummary] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if self.total_amount is None:
            self.total_amount = self.subtotal_at_proposal + self.shipping_amount + self.tax_amount
        if self.updated_at is None:
            self.updated_at = self.created_at


class ProposalRejectRequest(BaseModel):
    """Request payload for rejecting an active proposal."""

    reason: Optional[str] = Field("user_rejected", max_length=256, description="Reason for rejecting proposal")


class ProposalCreateRequest(BaseModel):
    """Request payload to create a proposal from an eligible candidate."""

    request_id: uuid.UUID
    candidate_id: uuid.UUID
    offer_id: Optional[uuid.UUID] = None
    quantity: int = Field(1, ge=1, le=10)
    rationale: Optional[str] = None


class CheckoutPreparationResult(BaseModel):
    """Trusted result returned by B9 for B10 PayPal order initiation."""

    proposal_id: uuid.UUID
    user_id: uuid.UUID
    mandate_id: uuid.UUID
    mandate_version: int
    amount: Decimal
    currency: str
    is_eligible: bool
    offer_domain: str
    product_title: str
    available_budget_remaining: Decimal


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
    approval_url: Optional[str] = None
