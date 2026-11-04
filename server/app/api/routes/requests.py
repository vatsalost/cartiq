"""Shopping request endpoints and Server-Sent Events (SSE) streaming."""

import asyncio
from datetime import datetime, timezone
import json
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import StreamingResponse
from server.app.api.dependencies import (
    get_candidate_service,
    get_current_user,
    get_request_service,
)
from server.app.core.rate_limit import rate_limit, request_creation_limiter
from server.app.core.security import AuthenticatedUser
from server.app.schemas.candidate import CandidateListResponse, CandidateResponse
from server.app.schemas.request import (
    RequestCancelResponse,
    RequestCreate,
    RequestCreateResponse,
    RequestDetailResponse,
)
from server.app.services.candidate_service import CandidateService
from server.app.services.event_bus import event_bus
from server.app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post(
    "",
    response_model=RequestCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit(request_creation_limiter))],
    summary="Submit a natural language shopping request",
    description="Validates active mandate, queues request, snapshots mandate version, and returns stream URL.",
)
async def create_request(
    request_in: RequestCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    created_request = request_service.create_request(current_user.id, request_in)
    return RequestCreateResponse(
        request_id=created_request.id,
        status=created_request.status,
        stream_url=f"/api/requests/{created_request.id}/stream",
    )


@router.get(
    "/{request_id}",
    response_model=RequestDetailResponse,
    summary="Get shopping request status",
    description="Loads request status, original parameters, and snapshot mandate version.",
)
async def get_request(
    request_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    req = request_service.get_request(request_id, current_user.id)
    return RequestDetailResponse(
        id=req.id,
        user_id=req.user_id,
        mandate_id=req.mandate_id,
        mandate_version=req.mandate.version if req.mandate else 1,
        request_text=req.request_text,
        normalized_intent=req.normalized_intent,
        status=req.status,
        error_code=req.error_code,
        error_details=req.error_details,
        processing_started_at=req.processing_started_at,
        completed_at=req.completed_at,
        retry_count=req.retry_count,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.get(
    "/{request_id}/stream",
    summary="Stream agent progress via Server-Sent Events (SSE)",
    description="Streams real-time agent milestones and replays missed events with event IDs.",
)
async def stream_request_progress(
    request: Request,
    request_id: uuid.UUID,
    last_event_id: Optional[int] = Query(None),
    last_event_header: Optional[str] = Header(None, alias="Last-Event-ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    # Ownership verification
    req = request_service.get_request(request_id, current_user.id)

    # Determine since_id for replay
    since_id = last_event_id
    if since_id is None and last_event_header:
        try:
            since_id = int(last_event_header)
        except ValueError:
            pass

    async def event_generator():
        # 1. First subscribe to pub/sub to guarantee zero missed events
        queue = await event_bus.subscribe(request_id)
        latest_replayed_id = since_id or 0
        try:
            # 2. Replay historical stored events
            history = request_service.get_request_events(
                request_id, since_id=since_id, user_id=current_user.id
            )
            terminal_seen = False

            for ev in history:
                latest_replayed_id = max(latest_replayed_id, ev.id)
                payload_json = json.dumps(ev.payload)
                yield f"id: {ev.id}\nevent: {ev.event_type}\ndata: {payload_json}\n\n"
                if ev.event_type in (
                    "proposal_ready",
                    "request_blocked",
                    "request_failed",
                    "request_cancelled",
                    "no_match",
                ):
                    terminal_seen = True
                    break

            if terminal_seen:
                return

            # 3. Stream real-time events as they arrive
            while True:
                # Check client disconnection
                if await request.is_disconnected():
                    break

                try:
                    # Wait up to 15 seconds for next event before sending a heartbeat
                    ev_dto = await asyncio.wait_for(queue.get(), timeout=15.0)

                    # Skip if already replayed
                    if ev_dto.id <= latest_replayed_id:
                        continue

                    payload_json = json.dumps(ev_dto.payload)
                    yield f"id: {ev_dto.id}\nevent: {ev_dto.event_type}\ndata: {payload_json}\n\n"

                    # Stop if terminal event
                    if ev_dto.event_type in (
                        "proposal_ready",
                        "request_blocked",
                        "request_failed",
                        "request_cancelled",
                        "no_match",
                    ):
                        break

                except asyncio.TimeoutError:
                    # Periodic SSE heartbeat
                    heartbeat_payload = json.dumps({
                        "request_id": str(request_id),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    yield f"event: heartbeat\ndata: {heartbeat_payload}\n\n"

        finally:
            await event_bus.unsubscribe(request_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{request_id}/cancel",
    response_model=RequestCancelResponse,
    summary="Cancel active shopping request",
    description="Halts agent search and updates request state to cancelled.",
)
async def cancel_request(
    request_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    cancelled_request = request_service.cancel_request(request_id, current_user.id)
    return RequestCancelResponse(
        request_id=cancelled_request.id,
        status="cancelled",
        message="Shopping request has been cancelled.",
        cancelled_at=datetime.now(timezone.utc),
    )


@router.get(
    "/{request_id}/candidates",
    response_model=CandidateListResponse,
    summary="Get candidate products and retailer offers",
    description="Returns candidate items evaluated by the agent for comparison view.",
)
async def get_candidates(
    request_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
):
    candidates = candidate_service.get_candidates_for_request(request_id, current_user.id)
    candidate_responses = [CandidateResponse.model_validate(c) for c in candidates]
    return CandidateListResponse(
        request_id=request_id,
        candidates=candidate_responses,
    )
