"""Audit schemas for serialization of compliance and observability events."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    """Canonical audit event schema returned by API."""

    id: uuid.UUID
    user_id: uuid.UUID
    request_id: Optional[uuid.UUID] = None
    proposal_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    event_type: str
    actor: str = "system"
    decision: Optional[str] = None
    reason: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
