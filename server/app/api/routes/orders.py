"""Order checkout capture, refund, and history endpoints."""

from datetime import datetime, timezone
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from server.app.api.dependencies import get_current_user, get_order_service
from server.app.core.security import AuthenticatedUser
from server.app.schemas.order import (
    OrderCaptureRequest,
    OrderCaptureResponse,
    OrderDetailResponse,
    OrderListResponse,
)
from server.app.schemas.refund import RefundRequest, RefundResponse
from server.app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/{order_id}/capture",
    response_model=OrderCaptureResponse,
    summary="Capture PayPal order payment",
    description="Captures the authorized PayPal transaction server-side after buyer approval.",
)
async def capture_order(
    order_id: uuid.UUID,
    capture_in: Optional[OrderCaptureRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    paypal_order_id = capture_in.paypal_order_id if capture_in else None
    order = order_service.capture_order(order_id, current_user.id, paypal_order_id)
    return OrderCaptureResponse(
        order_id=order.id,
        paypal_order_id=order.paypal_order_id or "",
        paypal_capture_id=order.paypal_capture_id or "",
        status=order.status,
        amount=order.amount,
        currency=order.currency,
        captured_at=order.captured_at or datetime.now(timezone.utc),
    )


@router.post(
    "/{order_id}/refund",
    response_model=RefundResponse,
    summary="Refund completed order payment",
    description="Issues a full refund through PayPal for an eligible captured order.",
)
async def refund_order(
    order_id: uuid.UUID,
    refund_in: Optional[RefundRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    reason = refund_in.reason if refund_in else None
    refund = order_service.refund_order(order_id, current_user.id, reason)
    return RefundResponse(
        refund_id=refund.id,
        order_id=refund.order_id,
        paypal_refund_id=refund.paypal_refund_id,
        amount=refund.amount,
        currency=refund.currency,
        status=refund.status,
        created_at=refund.created_at,
    )


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List order history",
    description="Returns a paginated list of purchase transactions for the current user.",
)
async def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    items, total = order_service.list_orders(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    return OrderListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get single order receipt",
    description="Loads complete receipt, transaction timestamps, external retailer links, and refund status.",
)
async def get_order_receipt(
    order_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    receipt = order_service.get_order_receipt(order_id, current_user.id)
    return receipt


@router.post(
    "/{order_id}/cancel",
    response_model=OrderDetailResponse,
    summary="Cancel uncaptured in-flight order",
    description="Cancels an order awaiting approval and releases the reserved mandate budget.",
)
async def cancel_order(
    order_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    order = order_service.cancel_order(order_id, current_user.id)
    return order_service.get_order_receipt(order.id, current_user.id)


@router.post(
    "/{order_id}/reconcile",
    response_model=OrderDetailResponse,
    summary="Reconcile order state with PayPal",
    description="Synchronizes internal order state with the latest status from PayPal API.",
)
async def reconcile_order(
    order_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    order = order_service.reconcile_order_with_paypal(order_id, current_user.id)
    return order_service.get_order_receipt(order.id, current_user.id)
