"""Mandate management endpoints."""

import uuid
from fastapi import APIRouter, Depends, status
from server.app.api.dependencies import get_current_user, get_mandate_service
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.core.security import AuthenticatedUser
from server.app.schemas.mandate import BudgetBreakdown, MandateCreate, MandateResponse
from server.app.services.mandate_service import MandateService

router = APIRouter(prefix="/mandates", tags=["Mandates"])


@router.get(
    "/current",
    response_model=MandateResponse,
    summary="Get current active mandate",
    description="Loads the active spending mandate version for the authenticated user, including budget metrics.",
)
@router.get(
    "/active",
    response_model=MandateResponse,
    summary="Get current active mandate (alias)",
    description="Alias for /mandates/current for API consistency.",
)
async def get_current_mandate(
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    mandate = mandate_service.get_current_mandate(current_user.id)
    if not mandate:
        raise CartiAPIException(
            code=CartiErrorCode.MANDATE_NOT_FOUND,
            message="No active spending mandate found for this user.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return mandate_service.format_mandate_response(mandate)


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset all mandates and associated state for authenticated user",
    description="Wipes all mandates, proposals, and orders so the user can define everything from scratch.",
)
async def reset_mandate(
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    from server.app.models.mandate import Mandate
    from server.app.models.order import Order
    from server.app.models.proposal import Proposal
    mandate_service.db.query(Order).filter(Order.user_id == current_user.id).delete()
    mandate_service.db.query(Proposal).filter(Proposal.user_id == current_user.id).delete()
    mandate_service.db.query(Mandate).filter(Mandate.user_id == current_user.id).delete()
    mandate_service.db.commit()
    return {"status": "ok", "message": "Mandate reset successfully. Clean slate activated."}


@router.post(
    "",
    response_model=MandateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update spending mandate",
    description="Creates a new mandate version with deterministic constraints, superseding prior versions.",
)
async def create_mandate(
    mandate_in: MandateCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    new_mandate = mandate_service.create_or_update_mandate(current_user.id, mandate_in)
    return mandate_service.format_mandate_response(new_mandate)


@router.get(
    "/current/budget",
    response_model=BudgetBreakdown,
    summary="Get current available budget breakdown",
    description="Calculates authoritative budget breakdown: total, captured, reserved, and available.",
)
async def get_current_budget(
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    mandate = mandate_service.get_current_mandate(current_user.id)
    if not mandate:
        raise CartiAPIException(
            code=CartiErrorCode.MANDATE_NOT_FOUND,
            message="No active spending mandate found for this user.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return mandate_service.calculate_available_budget(mandate.id)


@router.get(
    "/versions/{version}",
    response_model=MandateResponse,
    summary="Get historical mandate version",
    description="Retrieves a specific historical mandate version for the authenticated user.",
)
async def get_mandate_version(
    version: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    mandate = mandate_service.get_mandate_version(
        identifier=current_user.id,
        version=version,
        user_id=current_user.id,
    )
    return mandate_service.format_mandate_response(mandate)


@router.post(
    "/{mandate_id}/revoke",
    response_model=MandateResponse,
    summary="Revoke spending mandate",
    description="Revokes an active mandate, preventing any further requests or checkout orders under it.",
)
async def revoke_mandate(
    mandate_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    revoked = mandate_service.revoke_mandate(mandate_id, user_id=current_user.id)
    return mandate_service.format_mandate_response(revoked)


@router.get(
    "/{mandate_id}",
    response_model=MandateResponse,
    summary="Get mandate by ID",
    description="Retrieves a specific mandate record by ID with ownership verification.",
)
async def get_mandate_by_id(
    mandate_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    mandate_service: MandateService = Depends(get_mandate_service),
):
    mandate = mandate_service.get_mandate_by_id(mandate_id, user_id=current_user.id)
    return mandate_service.format_mandate_response(mandate)
