"""Proposal review and PayPal order creation endpoints."""

import uuid
from fastapi import APIRouter, Depends, status
from server.app.api.dependencies import (
    get_current_user,
    get_order_service,
    get_proposal_service,
)
from server.app.core.security import AuthenticatedUser
from server.app.schemas.proposal import (
    ProposalCreateOrderRequest,
    ProposalCreateOrderResponse,
    ProposalOfferSummary,
    ProposalProductSummary,
    ProposalResponse,
)
from server.app.services.order_service import OrderService
from server.app.services.proposal_service import ProposalService

router = APIRouter(prefix="/proposals", tags=["Proposals"])


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

    return ProposalResponse(
        id=proposal.id,
        request_id=proposal.request_id,
        user_id=proposal.user_id,
        mandate_id=proposal.mandate_id,
        mandate_version=proposal.mandate.version if proposal.mandate else 1,
        candidate_id=proposal.candidate_id,
        offer_id=proposal.offer_id,
        quantity=proposal.quantity,
        unit_price_at_proposal=proposal.unit_price_at_proposal,
        subtotal_at_proposal=proposal.subtotal_at_proposal,
        currency=proposal.currency,
        rationale=proposal.rationale,
        guardrail_result=proposal.guardrail_result,
        verification_result=proposal.verification_result,
        status=proposal.status,
        expires_at=proposal.expires_at,
        created_at=proposal.created_at,
        product=product_summary,
        offer=offer_summary,
    )


@router.post(
    "/{proposal_id}/order",
    response_model=ProposalCreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create PayPal order for approved proposal",
    description="Revalidates proposal facts, reserves mandate budget, and creates a server-side PayPal Sandbox order.",
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
    )
