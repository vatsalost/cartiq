"""Candidate product and offer schemas for comparison view."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class CandidateOfferResponse(BaseModel):
    """Specific retailer offer for a candidate product."""

    id: uuid.UUID
    candidate_id: uuid.UUID
    provider_offer_id: Optional[str] = None
    domain: str
    buy_url: str
    price_amount: Decimal
    currency: str
    availability: str
    condition: str
    variant_data: Optional[Dict[str, Any]] = None
    is_eligible: bool
    rejection_reason: Optional[str] = None
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateResponse(BaseModel):
    """Candidate product returned for user comparison."""

    id: uuid.UUID
    request_id: uuid.UUID
    provider_product_id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    attributes: Dict[str, Any] = {}
    rank_score: Optional[Decimal] = None
    rank_reason: Optional[str] = None
    rejected_reason: Optional[str] = None
    observed_at: datetime
    offers: List[CandidateOfferResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CandidateListResponse(BaseModel):
    """Response containing all candidates evaluated for a request."""

    request_id: uuid.UUID
    candidates: List[CandidateResponse]
