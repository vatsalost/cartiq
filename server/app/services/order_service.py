"""Order service managing PayPal order creation, captures, refunds, and receipts."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import logging
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.refund import Refund
from server.app.schemas.order import OrderDetailResponse, OrderListItemResponse, OrderRefundSummary
from server.app.services.audit_service import AuditService
from server.app.services.mandate_service import MandateService
from server.app.services.paypal_service import paypal_service
from server.app.services.proposal_service import ProposalService

logger = logging.getLogger("carti.orders")


class OrderService:
    """Authoritative business logic for orders, payment capture, and refund reconciliation."""

    def __init__(self, db: Session):
        self.db = db
        self.mandate_service = MandateService(db)
        self.proposal_service = ProposalService(db)
        self.audit_service = AuditService(db)

    def create_order_from_proposal(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID, checkout_attempt_id: str
    ) -> Order:
        """
        Validate proposal via B9 checkout preparation, check budget, and create internal and PayPal orders.
        Server calculates all amounts; client cannot send amount/currency.
        """
        create_req_id = hashlib.sha256(f"{proposal_id}:{checkout_attempt_id}".encode("utf-8")).hexdigest()[:32]

        # Check if an order already exists for this proposal (idempotency guard)
        existing_order = self.db.scalars(
            select(Order).where(Order.proposal_id == proposal_id)
        ).first()
        if existing_order:
            if existing_order.user_id != user_id:
                raise CartiAPIException(
                    code=CartiErrorCode.ACCESS_DENIED,
                    message="You do not have permission to access this order.",
                    status_code=403,
                )
            if existing_order.create_request_id == create_req_id:
                return existing_order
            raise CartiAPIException(
                code=CartiErrorCode.PROPOSAL_STALE,
                message=f"Proposal {proposal_id} is already associated with an order ({existing_order.id}).",
                status_code=409,
            )

        # 1. B9 Trusted Checkout Preparation (revalidates ownership, proposal, mandate, currency, stock, tolerance, budget)
        prep = self.proposal_service.prepare_proposal_for_checkout(proposal_id, user_id)
        proposal = self.proposal_service.get_proposal(proposal_id, user_id)

        # 2. Call centralized PayPal Orders v2 API
        create_res = paypal_service.create_order(proposal, checkout_attempt_id)
        paypal_order_id = create_res[0]

        # 3. Persist Order with trusted B9 amount
        order = Order(
            proposal_id=proposal.id,
            user_id=user_id,
            paypal_order_id=paypal_order_id,
            create_request_id=create_req_id,
            amount=prep.amount,
            currency=prep.currency,
            status="created",
            budget_reserved=prep.amount,
        )
        self.db.add(order)
        proposal.status = "checkout_started"
        self.db.commit()
        self.db.refresh(order)

        self.audit_service.record_event(
            user_id=user_id,
            proposal_id=proposal.id,
            order_id=order.id,
            event_type="paypal_order_created",
            details={
                "paypal_order_id": paypal_order_id,
                "amount": str(prep.amount),
                "currency": prep.currency,
            },
        )
        return order

    def capture_order(
        self, order_id: uuid.UUID, user_id: uuid.UUID, paypal_order_id: Optional[str] = None
    ) -> Order:
        """Capture payment after buyer onApprove confirmation."""
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            order = self.db.scalars(
                select(Order).where(Order.id == order_id).with_for_update()
            ).first()
        else:
            order = self.db.get(Order, order_id)

        if not order:
            raise CartiAPIException(
                code=CartiErrorCode.ORDER_NOT_FOUND,
                message=f"Order {order_id} not found.",
                status_code=404,
            )
        if order.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to capture this order.",
                status_code=403,
            )

        # Validate PayPal order ID if provided in capture request
        if paypal_order_id and order.paypal_order_id and paypal_order_id != order.paypal_order_id:
            raise CartiAPIException(
                code=CartiErrorCode.PAYMENT_CAPTURE_FAILED,
                message="PayPal order ID mismatch: provided ID does not match internal order record.",
                status_code=400,
            )

        # Idempotent capture check
        if order.status == "completed":
            return order

        if order.status not in ["created", "buyer_approved"]:
            raise CartiAPIException(
                code=CartiErrorCode.PAYMENT_CAPTURE_FAILED,
                message=f"Cannot capture order in state '{order.status}'.",
                status_code=400,
            )

        capture_key = hashlib.sha256(f"cap:{order.id}".encode("utf-8")).hexdigest()[:32]

        capture_id, _, _, captured_at = paypal_service.capture_order(
            order.paypal_order_id, capture_key
        )

        order.paypal_capture_id = capture_id
        order.capture_request_id = capture_key
        order.captured_at = captured_at

        # Transition proposal status to ordered
        if order.proposal:
            order.proposal.status = "ordered"

        # B3 accounting: convert in-flight reservation to captured spend
        self.mandate_service.convert_reservation_to_captured(order.id)

        self.db.commit()
        self.db.refresh(order)

        self.audit_service.record_event(
            user_id=user_id,
            order_id=order.id,
            event_type="payment_captured",
            details={
                "paypal_capture_id": capture_id,
                "amount": str(order.amount),
                "currency": order.currency,
            },
        )
        return order

    def refund_order(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
        amount: Optional[Decimal] = None,
    ) -> Refund:
        """Execute full or partial refund for a captured Sandbox order."""
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            order = self.db.scalars(
                select(Order).where(Order.id == order_id).with_for_update()
            ).first()
        else:
            order = self.db.get(Order, order_id)

        if not order:
            raise CartiAPIException(
                code=CartiErrorCode.ORDER_NOT_FOUND,
                message=f"Order {order_id} not found.",
                status_code=404,
            )
        if order.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to refund this order.",
                status_code=403,
            )

        if order.status != "completed":
            raise CartiAPIException(
                code=CartiErrorCode.REFUND_NOT_ALLOWED,
                message=f"Cannot refund order in state '{order.status}'. Only completed captured orders can be refunded.",
                status_code=400,
            )

        if not order.paypal_capture_id:
            raise CartiAPIException(
                code=CartiErrorCode.REFUND_NOT_ALLOWED,
                message="Order has no PayPal capture ID associated to refund.",
                status_code=400,
            )

        # Check existing refunds
        completed_refunds = [r for r in order.refunds if r.status == "completed"]
        already_refunded = sum((r.amount for r in completed_refunds), Decimal("0.00"))
        remaining_capturable = order.amount - already_refunded

        refund_amount = amount if amount is not None else remaining_capturable
        if refund_amount <= Decimal("0.00"):
            raise CartiAPIException(
                code=CartiErrorCode.REFUND_NOT_ALLOWED,
                message="Refund amount must be greater than zero.",
                status_code=400,
            )
        if refund_amount > remaining_capturable:
            raise CartiAPIException(
                code=CartiErrorCode.REFUND_NOT_ALLOWED,
                message=f"Requested refund amount ({refund_amount}) exceeds remaining captured order amount ({remaining_capturable}).",
                status_code=400,
            )

        refund_key = hashlib.sha256(f"ref:{order.id}:{refund_amount}".encode("utf-8")).hexdigest()[:32]

        existing_refund = self.db.scalars(
            select(Refund).where(Refund.request_idempotency_key == refund_key)
        ).first()
        if existing_refund and existing_refund.status == "completed":
            return existing_refund

        paypal_refund_id, refund_status = paypal_service.refund_capture(
            order.paypal_capture_id, refund_amount, order.currency, refund_key, note_to_payer=reason
        )

        refund = Refund(
            order_id=order.id,
            paypal_refund_id=paypal_refund_id,
            request_idempotency_key=refund_key,
            amount=refund_amount,
            currency=order.currency,
            status=refund_status,
        )
        self.db.add(refund)

        if already_refunded + refund_amount >= order.amount:
            order.status = "refunded"
            order.budget_reserved = Decimal("0.00")

        self.db.commit()
        self.db.refresh(refund)

        self.audit_service.record_event(
            user_id=user_id,
            order_id=order.id,
            event_type="order_refunded",
            details={
                "paypal_refund_id": paypal_refund_id,
                "amount": str(refund_amount),
                "reason": reason,
            },
        )
        return refund

    def cancel_order(
        self, order_id: uuid.UUID, user_id: uuid.UUID, reason: str = "user_cancelled"
    ) -> Order:
        """Cancel an in-flight uncaptured order and release its budget reservation."""
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            order = self.db.scalars(
                select(Order).where(Order.id == order_id).with_for_update()
            ).first()
        else:
            order = self.db.get(Order, order_id)

        if not order:
            raise CartiAPIException(
                code=CartiErrorCode.ORDER_NOT_FOUND,
                message=f"Order {order_id} not found.",
                status_code=404,
            )
        if order.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to cancel this order.",
                status_code=403,
            )
        if order.status == "completed":
            raise CartiAPIException(
                code=CartiErrorCode.VALIDATION_ERROR,
                message="Cannot cancel a completed order. Request a refund instead.",
                status_code=400,
            )
        if order.status in ["cancelled", "failed"]:
            return order

        order.status = "cancelled"
        self.mandate_service.release_budget_reservation(order.id, reason=reason)
        if order.proposal and order.proposal.status == "checkout_started":
            order.proposal.status = "pending"

        self.db.commit()
        self.audit_service.record_event(
            user_id=user_id,
            order_id=order.id,
            event_type="order_cancelled",
            reason=reason,
        )
        return order

    def reconcile_order_with_paypal(self, order_id: uuid.UUID, user_id: uuid.UUID) -> Order:
        """Synchronize internal order status with live PayPal Orders v2 API."""
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            order = self.db.scalars(
                select(Order).where(Order.id == order_id).with_for_update()
            ).first()
        else:
            order = self.db.get(Order, order_id)

        if not order:
            raise CartiAPIException(
                code=CartiErrorCode.ORDER_NOT_FOUND,
                message=f"Order {order_id} not found.",
                status_code=404,
            )
        if order.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to access this order.",
                status_code=403,
            )

        if not order.paypal_order_id:
            return order

        details = paypal_service.get_order(order.paypal_order_id)
        pp_status = details.get("status", "").upper()

        if pp_status == "APPROVED" and order.status == "created":
            order.status = "buyer_approved"
            self.db.commit()
            self.audit_service.record_event(
                user_id=user_id,
                order_id=order.id,
                event_type="order_reconciled",
                details={"paypal_status": pp_status, "new_internal_status": order.status},
            )
        elif pp_status == "COMPLETED" and order.status not in ["completed", "refunded"]:
            order.captured_at = order.captured_at or datetime.now(timezone.utc)
            if not order.paypal_capture_id:
                try:
                    captures = (
                        details.get("purchase_units", [{}])[0]
                        .get("payments", {})
                        .get("captures", [])
                    )
                    if captures:
                        order.paypal_capture_id = captures[0].get("id")
                except Exception:
                    pass
                if not order.paypal_capture_id:
                    order.paypal_capture_id = f"CAP-REC-{order.paypal_order_id[-8:]}"

            self.mandate_service.convert_reservation_to_captured(order.id)
            if order.proposal:
                order.proposal.status = "ordered"
            self.db.commit()
            self.audit_service.record_event(
                user_id=user_id,
                order_id=order.id,
                event_type="order_reconciled",
                details={"paypal_status": pp_status, "new_internal_status": order.status},
            )

        return order

    def get_order_receipt(self, order_id: uuid.UUID, user_id: uuid.UUID) -> OrderDetailResponse:
        """Fetch detailed order receipt including product and refund info."""
        order = self.db.get(Order, order_id)
        if not order:
            raise CartiAPIException(
                code=CartiErrorCode.ORDER_NOT_FOUND,
                message=f"Order {order_id} not found.",
                status_code=404,
            )
        if order.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to view this order.",
                status_code=403,
            )

        if order.proposal and order.proposal.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Access denied: Associated proposal ownership mismatch.",
                status_code=403,
            )

        proposal = self.db.get(Proposal, order.proposal_id)
        product_title = None
        retailer_domain = None
        retailer_buy_url = None
        quantity = 1
        if proposal:
            quantity = proposal.quantity
            if proposal.candidate:
                product_title = proposal.candidate.title
            if proposal.offer:
                retailer_domain = proposal.offer.domain
                retailer_buy_url = proposal.offer.buy_url

        refunds_stmt = select(Refund).where(Refund.order_id == order_id)
        refunds = self.db.scalars(refunds_stmt).all()
        refund_summaries = [OrderRefundSummary.model_validate(r) for r in refunds]

        return OrderDetailResponse(
            id=order.id,
            proposal_id=order.proposal_id,
            user_id=order.user_id,
            paypal_order_id=order.paypal_order_id,
            paypal_capture_id=order.paypal_capture_id,
            amount=order.amount,
            currency=order.currency,
            status=order.status,
            budget_reserved=order.budget_reserved,
            captured_at=order.captured_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
            product_title=product_title,
            retailer_domain=retailer_domain,
            retailer_buy_url=retailer_buy_url,
            quantity=quantity,
            refunds=refund_summaries,
        )

    def list_orders(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Tuple[List[OrderListItemResponse], int]:
        """Fetch paginated order history with filtering."""
        query = select(Order).where(Order.user_id == user_id)
        if status:
            query = query.where(Order.status == status)
        if from_date:
            query = query.where(Order.created_at >= from_date)
        if to_date:
            query = query.where(Order.created_at <= to_date)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_stmt) or 0

        paged_stmt = query.order_by(Order.created_at.desc()).limit(limit).offset(offset)
        orders = self.db.scalars(paged_stmt).all()

        items = []
        for o in orders:
            proposal = self.db.get(Proposal, o.proposal_id)
            title = proposal.candidate.title if proposal and proposal.candidate else None
            domain = proposal.offer.domain if proposal and proposal.offer else None
            items.append(
                OrderListItemResponse(
                    id=o.id,
                    proposal_id=o.proposal_id,
                    paypal_order_id=o.paypal_order_id,
                    paypal_capture_id=o.paypal_capture_id,
                    amount=o.amount,
                    currency=o.currency,
                    status=o.status,
                    product_title=title,
                    retailer_domain=domain,
                    captured_at=o.captured_at,
                    created_at=o.created_at,
                )
            )

        return (items, total)
