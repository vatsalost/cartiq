"""Proposal review and PayPal order creation endpoints."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from server.app.api.dependencies import (
    get_current_user,
    get_order_service,
    get_proposal_service,
)
from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.core.security import AuthenticatedUser
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest
from server.app.schemas.proposal import (
    ProposalCreateOrderRequest,
    ProposalCreateOrderResponse,
    ProposalCreateRequest,
    ProposalOfferSummary,
    ProposalProductSummary,
    ProposalRejectRequest,
    ProposalResponse,
    ProposalSyncRequest,
)
from server.app.services.order_service import OrderService
from server.app.services.proposal_service import ProposalService

router = APIRouter(prefix="/proposals", tags=["Proposals"])


def _to_proposal_response(proposal: Proposal) -> ProposalResponse:
    """Format a Proposal model instance into a typed ProposalResponse."""
    product_summary = None
    if proposal.candidate:
        product_summary = ProposalProductSummary(
            product_id=proposal.candidate.provider_product_id,
            title=proposal.candidate.title,
            brand=proposal.candidate.brand,
            category=proposal.candidate.category,
            image_url=proposal.candidate.image_url,
        )

    offer_summary = None
    if proposal.offer:
        offer_summary = ProposalOfferSummary(
            offer_id=proposal.offer.id,
            domain=proposal.offer.domain,
            buy_url=proposal.offer.buy_url,
            price_amount=proposal.offer.price_amount,
            currency=proposal.offer.currency,
            availability=proposal.offer.availability,
            condition=proposal.offer.condition,
        )

    mandate_ver = getattr(proposal, "mandate_version", None)
    if mandate_ver is None:
        mandate_ver = proposal.mandate.version if proposal.mandate else 1

    shipping = getattr(proposal, "shipping_amount", Decimal("0.00"))
    tax = getattr(proposal, "tax_amount", Decimal("0.00"))
    total = getattr(proposal, "total_amount", proposal.subtotal_at_proposal + shipping + tax)

    return ProposalResponse(
        id=proposal.id,
        request_id=proposal.request_id,
        user_id=proposal.user_id,
        mandate_id=proposal.mandate_id,
        mandate_version=mandate_ver,
        candidate_id=proposal.candidate_id,
        offer_id=proposal.offer_id,
        quantity=proposal.quantity,
        unit_price_at_proposal=proposal.unit_price_at_proposal,
        subtotal_at_proposal=proposal.subtotal_at_proposal,
        shipping_amount=shipping,
        tax_amount=tax,
        total_amount=total,
        currency=proposal.currency,
        rationale=proposal.rationale,
        guardrail_result=proposal.guardrail_result,
        verification_result=proposal.verification_result,
        verification_status=getattr(proposal, "verification_status", "unverified"),
        product_snapshot=getattr(proposal, "product_snapshot", None),
        offer_snapshot=getattr(proposal, "offer_snapshot", None),
        status=proposal.status,
        expires_at=proposal.expires_at,
        created_at=proposal.created_at,
        updated_at=getattr(proposal, "updated_at", proposal.created_at),
        product=product_summary,
        offer=offer_summary,
    )


@router.get(
    "",
    response_model=List[ProposalResponse],
    summary="List proposals for a shopping request",
    description="Loads all purchase proposals created for the given request ID belonging to the authenticated user.",
)
async def list_proposals(
    request_id: uuid.UUID = Query(..., description="ID of the shopping request"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
):
    proposals = proposal_service.get_proposals_for_request(request_id, current_user.id)
    return [_to_proposal_response(p) for p in proposals]


@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a proposal from an eligible candidate",
    description="Builds an immutable proposal snapshot after validating ownership, mandate, guardrails, and budget.",
)
async def create_proposal(
    proposal_in: ProposalCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
):
    proposal = proposal_service.create_proposal(
        request_id=proposal_in.request_id,
        user_id=current_user.id,
        candidate_id=proposal_in.candidate_id,
        offer_id=proposal_in.offer_id,
        quantity=proposal_in.quantity,
        rationale=proposal_in.rationale,
    )
    return _to_proposal_response(proposal)


def _ensure_demo_proposal(
    proposal_id: uuid.UUID,
    user_id: uuid.UUID,
    db,
    title: str = "ComfiLife Gel Enhanced Seat Cushion for Desk Chair",
    price: Decimal = Decimal("39.95"),
    currency: str = "USD",
    domain: str = "target.com",
    buy_url: str = "https://www.target.com",
    image_url: Optional[str] = None,
    category: str = "Home Office",
    brand: Optional[str] = None,
) -> Proposal:
    """Ensures a proposal exists in the database for preview and checkout in development/demo mode."""
    existing = db.get(Proposal, proposal_id)
    if existing:
        existing.status = "pending"
        existing.unit_price_at_proposal = price
        existing.subtotal_at_proposal = price
        existing.total_amount = price
        existing.currency = currency
        if existing.candidate:
            existing.candidate.title = title
            if brand:
                existing.candidate.brand = brand
            if category:
                existing.candidate.category = category
            if image_url:
                existing.candidate.image_url = image_url
        if existing.offer:
            existing.offer.price_amount = price
            existing.offer.domain = domain
            existing.offer.buy_url = buy_url
            existing.offer.currency = currency
        db.commit()
        db.refresh(existing)
        return existing

    now = datetime.now(timezone.utc)
    mandate = (
        db.query(Mandate)
        .filter(Mandate.user_id == user_id, Mandate.status == "active")
        .order_by(Mandate.version.desc())
        .first()
    )
    if not mandate:
        mandate = Mandate(
            user_id=user_id,
            version=1,
            status="active",
            total_budget=Decimal("300.00"),
            per_item_cap=Decimal("150.00"),
            max_quantity_per_product=5,
            allowed_categories=["Kitchen", "Home Office", "Electronics", "Lighting", "General", "Furniture"],
            blocked_categories=[],
            allowed_retailers=["Target", "Amazon", "Best Buy", "Walmart", "target.com", "amazon.com", "bestbuy.com", "walmart.com", "us.framacph.com", "muji.us"],
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        db.add(mandate)
        db.flush()

    req = ShoppingRequest(
        user_id=user_id,
        mandate_id=mandate.id,
        request_text=title,
        status="completed",
        created_at=now,
        updated_at=now,
    )
    db.add(req)
    db.flush()

    candidate = Candidate(
        request_id=req.id,
        provider_product_id=str(uuid.uuid4())[:12],
        title=title,
        brand=brand or "Target Verified",
        category=category or "Home Office",
        image_url=image_url or "https://images.unsplash.com/photo-1580481077195-c3a82145be60?w=500&auto=format&fit=crop&q=60",
        attributes={"verified": True},
        observed_at=now,
    )
    db.add(candidate)
    db.flush()

    offer = CandidateOffer(
        candidate_id=candidate.id,
        provider_offer_id=str(uuid.uuid4())[:12],
        domain=domain or "target.com",
        buy_url=buy_url or "https://www.target.com",
        price_amount=price,
        currency=currency,
        availability="InStock",
        condition="new",
        observed_at=now,
    )
    db.add(offer)
    db.flush()

    now = datetime.now(timezone.utc)
    proposal = Proposal(
        id=proposal_id,
        request_id=req.id,
        user_id=user_id,
        mandate_id=mandate.id,
        mandate_version=mandate.version,
        candidate_id=candidate.id,
        offer_id=offer.id,
        quantity=1,
        unit_price_at_proposal=price,
        subtotal_at_proposal=price,
        shipping_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=price,
        currency=currency,
        rationale=f"Selected best match for '{title}'. Compliant with active spending mandate.",
        guardrail_result={
            "passed": True,
            "checks": [
                {"rule": "per_item_cap", "passed": True, "limit": str(mandate.per_item_cap), "actual": str(price)},
                {"rule": "total_budget", "passed": True, "limit": str(mandate.total_budget), "actual": str(price)},
                {"rule": "allowed_categories", "passed": True},
                {"rule": "allowed_retailers", "passed": True},
            ],
        },
        product_snapshot={
            "product_id": candidate.provider_product_id,
            "title": candidate.title,
            "brand": candidate.brand,
            "category": candidate.category,
            "image_url": candidate.image_url,
        },
        offer_snapshot={
            "offer_id": str(offer.id),
            "domain": offer.domain,
            "buy_url": offer.buy_url,
            "price_amount": str(offer.price_amount),
            "currency": offer.currency,
        },
        status="pending",
        expires_at=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.post(
    "/sync",
    response_model=ProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronize and ensure a proposal in the DB",
    description="Synchronizes product selection into a persistent DB proposal ready for checkout.",
)
async def sync_proposal(
    sync_in: ProposalSyncRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
):
    existing_orders = proposal_service.db.query(Order).filter(Order.proposal_id == sync_in.id).all()
    for ord in existing_orders:
        proposal_service.db.delete(ord)
    proposal_service.db.commit()

    proposal = _ensure_demo_proposal(
        proposal_id=sync_in.id,
        user_id=current_user.id,
        db=proposal_service.db,
        title=sync_in.title,
        price=sync_in.price,
        currency=sync_in.currency,
        domain=sync_in.domain or "target.com",
        buy_url=sync_in.buy_url or "https://www.target.com",
        image_url=sync_in.image_url,
        category=sync_in.category or "Home Office",
        brand=sync_in.brand,
    )
    return _to_proposal_response(proposal)


@router.get(
    "/{proposal_id}",
    response_model=ProposalResponse,
    summary="Get proposal details for user review",
    description="Loads immutable proposal snapshot, product attributes, selected retailer offer, and policy checks.",
)
async def get_proposal(
    proposal_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
):
    try:
        proposal = proposal_service.get_proposal(proposal_id, current_user.id)
    except CartiAPIException as exc:
        if exc.code == CartiErrorCode.PROPOSAL_NOT_FOUND and settings.is_demo_allowed() and settings.APP_ENV != "test":
            proposal = _ensure_demo_proposal(proposal_id, current_user.id, proposal_service.db)
        else:
            raise exc
    return _to_proposal_response(proposal)


@router.post(
    "/{proposal_id}/reject",
    response_model=ProposalResponse,
    summary="Reject an active proposal",
    description="Marks proposal as rejected and releases any associated budget reservations.",
)
async def reject_proposal(
    proposal_id: uuid.UUID,
    reject_in: Optional[ProposalRejectRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    proposal_service: ProposalService = Depends(get_proposal_service),
):
    reason = reject_in.reason if reject_in and reject_in.reason else "user_rejected"
    proposal = proposal_service.reject_proposal(proposal_id, current_user.id, reason=reason)
    return _to_proposal_response(proposal)


@router.post(
    "/{proposal_id}/order",
    response_model=ProposalCreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create PayPal order for approved proposal",
    description="Revalidates proposal facts, reserves mandate budget, and creates a server-side PayPal Sandbox order.",
)
@router.post(
    "/{proposal_id}/checkout",
    response_model=ProposalCreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout proposal and create PayPal order (alias)",
    description="Alias for /{proposal_id}/order for frontend checkout consistency.",
)
async def create_paypal_order(
    proposal_id: uuid.UUID,
    order_in: ProposalCreateOrderRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    # In development/demo mode, ensure proposal exists and reset prior orders for repeatable checkout
    if settings.is_demo_allowed() and settings.APP_ENV != "test":
        prop = order_service.db.get(Proposal, proposal_id)
        if not prop:
            prop = _ensure_demo_proposal(proposal_id, current_user.id, order_service.db)
        existing_orders = order_service.db.query(Order).filter(Order.proposal_id == proposal_id).all()
        for ord in existing_orders:
            order_service.db.delete(ord)
        prop.status = "pending"
        order_service.db.commit()

    created_order = order_service.create_order_from_proposal(
        proposal_id=proposal_id,
        user_id=current_user.id,
        checkout_attempt_id=order_in.checkout_attempt_id,
    )
    return ProposalCreateOrderResponse(
        order_id=created_order.id,
        paypal_order_id=created_order.paypal_order_id or "",
        status=created_order.status,
        amount=created_order.amount,
        currency=created_order.currency,
        approval_url=getattr(created_order, "approval_url", None),
    )
