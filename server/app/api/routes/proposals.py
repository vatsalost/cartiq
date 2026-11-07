"""Proposal review and PayPal order creation endpoints."""

from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from server.app.api.dependencies import (
    get_current_user,
    get_order_service,
    get_proposal_service,
)
from server.app.core.security import AuthenticatedUser
from server.app.models.proposal import Proposal
from server.app.schemas.proposal import (
    ProposalCreateOrderRequest,
    ProposalCreateOrderResponse,
    ProposalCreateRequest,
    ProposalOfferSummary,
    ProposalProductSummary,
    ProposalRejectRequest,
    ProposalResponse,
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
    proposal = proposal_service.get_proposal(proposal_id, current_user.id)
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
