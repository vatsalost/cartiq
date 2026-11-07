"""Webhook processing service for PayPal asynchronous notifications."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.order import Order
from server.app.models.webhook import WebhookEvent
from server.app.services.audit_service import AuditService
from server.app.services.mandate_service import MandateService
from server.app.services.paypal_service import paypal_service

logger = logging.getLogger("carti.webhooks")


class WebhookService:
    """Verifies, deduplicates, and applies monotonic transitions from PayPal webhooks."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.mandate_service = MandateService(db)

    def process_webhook(
        self, headers: Dict[str, str], raw_body: bytes, payload: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify incoming webhook signature, deduplicate provider_event_id,
        and reconcile internal order state.
        """
        # 1. Signature verification
        is_valid = paypal_service.verify_webhook_signature(headers, raw_body)
        if not is_valid:
            logger.warning("Rejected PayPal webhook with invalid signature.")
            raise CartiAPIException(
                code=CartiErrorCode.WEBHOOK_SIGNATURE_INVALID,
                message="PayPal webhook signature verification failed.",
                status_code=400,
            )

        event_id = payload.get("id")
        if not event_id:
            raise CartiAPIException(
                code=CartiErrorCode.VALIDATION_ERROR,
                message="Missing event ID in PayPal webhook payload.",
                status_code=400,
            )

        event_type = payload.get("event_type", "UNKNOWN")
        resource = payload.get("resource", {})
        resource_id = resource.get("id")

        # 2. Deduplication check
        existing_event = self.db.scalars(
            select(WebhookEvent).where(WebhookEvent.provider_event_id == event_id)
        ).first()
        if existing_event:
            logger.info("Ignoring duplicate PayPal webhook event: %s", event_id)
            return (True, event_id)

        # Record incoming event record
        webhook_record = WebhookEvent(
            provider_event_id=event_id,
            event_type=event_type,
            resource_id=resource_id,
            verified=True,
            processed=False,
            payload=payload,
        )
        self.db.add(webhook_record)
        self.db.commit()

        # 3. Monotonic order state reconciliation
        order = None
        if resource_id:
            # Check matching by capture id or order id
            order = self.db.scalars(
                select(Order).where(
                    (Order.paypal_capture_id == resource_id)
                    | (Order.paypal_order_id == resource_id)
                )
            ).first()

        if order:
            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                if order.status not in ["completed", "refunded"]:
                    order.status = "completed"
                    order.captured_at = datetime.now(timezone.utc)
                    if order.proposal:
                        order.proposal.status = "ordered"
                    self.mandate_service.convert_reservation_to_captured(order.id)
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                if order.status != "completed":
                    order.status = "failed"
                    self.mandate_service.release_budget_reservation(order.id, reason="paypal_capture_denied")
            elif event_type == "PAYMENT.CAPTURE.REFUNDED":
                order.status = "refunded"
                order.budget_reserved = Decimal("0.00")

            self.db.commit()
            self.audit_service.record_event(
                user_id=order.user_id,
                order_id=order.id,
                event_type=f"webhook_{event_type.lower()}",
                actor="paypal_webhook",
                details={"event_id": event_id, "resource_id": resource_id},
            )

        webhook_record.processed = True
        webhook_record.processed_at = datetime.now(timezone.utc)
        self.db.commit()

        return (True, event_id)
