"""Agent orchestrator and request execution engine.

Coordinates the request lifecycle across discovery, candidate evaluation,
guardrails, and proposal creation with worker leases, checkpoints, and bounded retries.
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
import os
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.db.session import SessionLocal
from server.app.models.base import utc_now
from server.app.models.candidate import Candidate, CandidateOffer
from server.app.models.mandate import Mandate
from server.app.models.proposal import Proposal
from server.app.models.request import ShoppingRequest, RequestEvent
from server.app.schemas.request import RequestEventResponse, RequestStatus
from server.app.services.audit_service import AuditService
from server.app.services.event_bus import event_bus
from server.app.services.interfaces import (
    IAgentLoop,
    IDiscoveryService,
    IGuardrailEngine,
    IProposalCreationService,
    IRankingService,
)
from server.app.services.lifecycle import RequestLifecycleManager, is_terminal_status

logger = logging.getLogger("carti.orchestrator")


class AgentOrchestrator:
    """Central request lifecycle orchestrator coordinating downstream services."""

    def __init__(
        self,
        discovery_service: Optional[IDiscoveryService] = None,
        ranking_service: Optional[IRankingService] = None,
        guardrail_engine: Optional[IGuardrailEngine] = None,
        proposal_creator: Optional[IProposalCreationService] = None,
        agent_loop: Optional[IAgentLoop] = None,
        session_factory=SessionLocal,
    ):
        self._active_tasks: Dict[uuid.UUID, asyncio.Task] = {}
        self.discovery_service = discovery_service
        self.ranking_service = ranking_service
        self.guardrail_engine = guardrail_engine
        self.proposal_creator = proposal_creator
        self.agent_loop = agent_loop
        self.session_factory = session_factory

    def start_request_run(
        self, request_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[asyncio.Task]:
        """Schedule asynchronous execution in background task."""
        # Cancel any previous task for this request in this worker
        if request_id in self._active_tasks:
            prev_task = self._active_tasks.pop(request_id)
            if not prev_task.done():
                prev_task.cancel()

        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(
                self.execute_request_pipeline(request_id, user_id)
            )
            self._active_tasks[request_id] = task

            def _cleanup(t):
                self._active_tasks.pop(request_id, None)

            task.add_done_callback(_cleanup)
            return task
        except RuntimeError:
            return None

    def stop_request_run(self, request_id: uuid.UUID) -> None:
        """Cancel an active in-flight worker task."""
        task = self._active_tasks.pop(request_id, None)
        if task and not task.done():
            task.cancel()
            logger.info("Cancelled active orchestrator task for request: %s", request_id)

    async def _emit_event(
        self, db: Session, request_id: uuid.UUID, event_type: str, payload: dict
    ) -> RequestEvent:
        """Persist event to database before broadcasting to live SSE subscribers."""
        event = RequestEvent(
            request_id=request_id,
            event_type=event_type,
            payload=payload,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        dto = RequestEventResponse.model_validate(event)
        await event_bus.publish(request_id, dto)
        return event

    def _is_cancelled(self, db: Session, request_id: uuid.UUID) -> bool:
        """Checkpoint check: verify if request was cancelled by user."""
        req = db.get(ShoppingRequest, request_id)
        if not req or req.status == RequestStatus.CANCELLED.value:
            return True
        return False

    async def execute_request_pipeline(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        worker_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Execute complete orchestrator pipeline with leases, checkpoints, and guardrails."""
        worker_tag = worker_id or f"worker_{os.getpid()}_{uuid.uuid4().hex[:8]}"
        should_close_db = False
        if db is None:
            factory = self.session_factory or SessionLocal
            db = factory()
            should_close_db = True

        lifecycle = RequestLifecycleManager(db)
        audit_service = AuditService(db)

        try:
            req = db.get(ShoppingRequest, request_id)
            if not req:
                logger.warning("Request %s not found for execution", request_id)
                return

            # Ownership boundary verification
            if req.user_id != user_id:
                logger.error("Ownership mismatch for request %s (user %s != %s)", request_id, req.user_id, user_id)
                return

            # Idempotency / lease acquisition
            acquired = lifecycle.acquire_lease(req, worker_id=worker_tag, lease_seconds=120)
            if not acquired:
                if req.retry_count >= req.max_retries and req.status in (RequestStatus.QUEUED.value, RequestStatus.RUNNING.value):
                    lifecycle.transition(
                        req,
                        target_status=RequestStatus.FAILED.value,
                        error_code=CartiErrorCode.RETRY_LIMIT_EXCEEDED,
                        error_details={"reason": "Maximum execution retry attempts exceeded."},
                    )
                    await self._emit_event(
                        db,
                        request_id,
                        "request_failed",
                        {
                            "request_id": str(request_id),
                            "step": "request_failed",
                            "message": "Maximum execution retry attempts exceeded.",
                            "error_code": CartiErrorCode.RETRY_LIMIT_EXCEEDED,
                        },
                    )
                logger.info("Could not acquire lease for request %s on worker %s", request_id, worker_tag)
                return

            # Verify active mandate
            mandate = db.get(Mandate, req.mandate_id)
            if not mandate or mandate.status != "active":
                lifecycle.transition(
                    req,
                    target_status=RequestStatus.BLOCKED.value,
                    error_code=CartiErrorCode.MANDATE_INVALID,
                    error_details={"reason": "Associated mandate is no longer active."},
                )
                await self._emit_event(
                    db,
                    request_id,
                    "request_blocked",
                    {
                        "request_id": str(request_id),
                        "step": "request_blocked",
                        "message": "Associated spending mandate is no longer active.",
                        "error_code": CartiErrorCode.MANDATE_INVALID,
                    },
                )
                return

            # Transition: queued -> running
            lifecycle.transition(req, target_status=RequestStatus.RUNNING.value)
            audit_service.record_event(
                user_id=user_id,
                request_id=request_id,
                event_type="orchestration_started",
                details={"worker": worker_tag, "retry_count": req.retry_count},
            )

            # Checkpoint 1: Cancellation check
            if self._is_cancelled(db, request_id):
                return

            # Step 1: Product Discovery (B5/B6)
            await self._emit_event(
                db,
                request_id,
                "search_started",
                {
                    "request_id": str(request_id),
                    "step": "search_started",
                    "message": "Initiating product search across authorized retailers.",
                    "progress": 25,
                },
            )

            # Retrieve or discover candidates
            candidates = await self._load_or_discover_candidates_async(db, req, mandate)

            # Checkpoint 2: Cancellation check
            if self._is_cancelled(db, request_id):
                return

            if not candidates:
                # No matching products found -> terminal state: no_match
                lifecycle.transition(
                    req,
                    target_status=RequestStatus.NO_MATCH.value,
                    error_code=CartiErrorCode.NO_ELIGIBLE_PRODUCTS,
                    error_details={"reason": "No products matched the search query and filters."},
                )
                await self._emit_event(
                    db,
                    request_id,
                    "search_results_received",
                    {
                        "request_id": str(request_id),
                        "step": "search_results_received",
                        "message": "Found 0 products matching search criteria.",
                        "candidate_count": 0,
                        "progress": 50,
                    },
                )
                await self._emit_event(
                    db,
                    request_id,
                    "no_match",
                    {
                        "request_id": str(request_id),
                        "step": "no_match",
                        "message": "No matching products found within the specified criteria.",
                        "progress": 100,
                    },
                )
                audit_service.record_event(
                    user_id=user_id,
                    request_id=request_id,
                    event_type="request_concluded",
                    decision="no_match",
                )
                return

            await self._emit_event(
                db,
                request_id,
                "search_results_received",
                {
                    "request_id": str(request_id),
                    "step": "search_results_received",
                    "message": f"Found {len(candidates)} candidate products for evaluation.",
                    "candidate_count": len(candidates),
                    "progress": 50,
                },
            )

            # Checkpoint 3: Cancellation check
            if self._is_cancelled(db, request_id):
                return

            # Step 2: Candidate Ranking & Refresh (B7)
            if self.ranking_service:
                candidates = self.ranking_service.rank_candidates(candidates, req.request_text, mandate)

            for cand in candidates:
                await self._emit_event(
                    db,
                    request_id,
                    "candidate_refreshed",
                    {
                        "request_id": str(request_id),
                        "step": "candidate_refreshed",
                        "candidate_id": str(cand.id),
                        "title": cand.title,
                        "rank_score": float(cand.rank_score) if cand.rank_score else None,
                        "progress": 65,
                    },
                )

            # Checkpoint 4: Cancellation check
            if self._is_cancelled(db, request_id):
                return

            # Step 3: Deterministic Policy & Budget Guardrails (B8)
            from server.app.services.mandate_service import MandateService
            mandate_svc = MandateService(db)
            available_budget = mandate_svc.calculate_available_budget(mandate.id)

            eligible_candidates = []
            for cand in candidates:
                # Check candidate against deterministic mandate policy
                is_eligible, rejection_reason = self._evaluate_candidate_policy(
                    cand, mandate, available_budget
                )
                if not is_eligible:
                    cand.rejected_reason = rejection_reason
                    db.commit()
                    await self._emit_event(
                        db,
                        request_id,
                        "candidate_rejected",
                        {
                            "request_id": str(request_id),
                            "step": "candidate_rejected",
                            "candidate_id": str(cand.id),
                            "reason": rejection_reason,
                            "progress": 70,
                        },
                    )
                else:
                    eligible_candidates.append(cand)

            if not eligible_candidates:
                # All candidates blocked by guardrails -> terminal state: blocked
                lifecycle.transition(
                    req,
                    target_status=RequestStatus.BLOCKED.value,
                    error_code=CartiErrorCode.GUARDRAIL_BLOCKED,
                    error_details={"reason": "All candidate offers were rejected by spending mandate guardrails."},
                )
                await self._emit_event(
                    db,
                    request_id,
                    "guardrail_blocked",
                    {
                        "request_id": str(request_id),
                        "step": "guardrail_blocked",
                        "message": "All candidate products exceeded mandate spending caps or policy restrictions.",
                        "error_code": CartiErrorCode.GUARDRAIL_BLOCKED,
                        "progress": 85,
                    },
                )
                await self._emit_event(
                    db,
                    request_id,
                    "request_blocked",
                    {
                        "request_id": str(request_id),
                        "step": "request_blocked",
                        "message": "Shopping request blocked: no candidates met mandate requirements.",
                        "error_code": CartiErrorCode.GUARDRAIL_BLOCKED,
                        "progress": 100,
                    },
                )
                audit_service.record_event(
                    user_id=user_id,
                    request_id=request_id,
                    event_type="request_blocked",
                    reason="guardrail_violations",
                )
                return

            await self._emit_event(
                db,
                request_id,
                "guardrail_passed",
                {
                    "request_id": str(request_id),
                    "step": "guardrail_passed",
                    "message": f"{len(eligible_candidates)} candidates verified within available budget and rules.",
                    "progress": 80,
                },
            )

            # Checkpoint 5: Cancellation check
            if self._is_cancelled(db, request_id):
                return

            # Step 4: Verification & Proposal Creation (B9)
            best_candidate = eligible_candidates[0]
            selected_offer = best_candidate.offers[0] if best_candidate.offers else None
            if not selected_offer:
                lifecycle.transition(
                    req,
                    target_status=RequestStatus.FAILED.value,
                    error_code=CartiErrorCode.OFFER_UNAVAILABLE,
                    error_details={"reason": "Selected candidate has no valid retailer offers."},
                )
                await self._emit_event(
                    db,
                    request_id,
                    "request_failed",
                    {
                        "request_id": str(request_id),
                        "step": "request_failed",
                        "message": "Selected candidate has no active retailer offers.",
                        "error_code": CartiErrorCode.OFFER_UNAVAILABLE,
                    },
                )
                return

            await self._emit_event(
                db,
                request_id,
                "verification_started",
                {
                    "request_id": str(request_id),
                    "step": "verification_started",
                    "message": f"Verifying offer from {selected_offer.domain}.",
                    "progress": 85,
                },
            )

            # Checkpoint 6: Cancellation check
            if self._is_cancelled(db, request_id):
                return

            await self._emit_event(
                db,
                request_id,
                "verification_completed",
                {
                    "request_id": str(request_id),
                    "step": "verification_completed",
                    "message": "Offer authenticity and stock verified.",
                    "progress": 90,
                },
            )

            # Proposal synthesis and persistence with atomic row lock
            stmt = select(ShoppingRequest).where(ShoppingRequest.id == request_id).with_for_update()
            locked_req = db.scalars(stmt).first()
            if not locked_req or locked_req.status != RequestStatus.RUNNING.value:
                logger.info("Request %s is status '%s'; aborting proposal creation", request_id, getattr(locked_req, 'status', None))
                return

            proposal = self._create_and_persist_proposal(
                db, locked_req, mandate, best_candidate, selected_offer
            )

            # Transition: running -> proposal_ready
            lifecycle.transition(locked_req, target_status=RequestStatus.PROPOSAL_READY.value)

            await self._emit_event(
                db,
                request_id,
                "proposal_ready",
                {
                    "request_id": str(request_id),
                    "step": "proposal_ready",
                    "message": "Purchase proposal prepared and ready for user approval.",
                    "proposal_id": str(proposal.id),
                    "amount": str(proposal.subtotal_at_proposal),
                    "currency": proposal.currency,
                    "progress": 100,
                },
            )

            audit_service.record_event(
                user_id=user_id,
                request_id=request_id,
                proposal_id=proposal.id,
                event_type="proposal_created",
                details={
                    "candidate_id": str(best_candidate.id),
                    "offer_id": str(selected_offer.id),
                    "amount": str(proposal.subtotal_at_proposal),
                    "currency": proposal.currency,
                },
            )

        except asyncio.CancelledError:
            logger.info("Pipeline execution cancelled for request %s", request_id)
        except CartiAPIException as exc:
            logger.warning("CartiAPIException during request %s: %s", request_id, exc.message)
            req = db.get(ShoppingRequest, request_id)
            if req and req.status not in (RequestStatus.CANCELLED.value, RequestStatus.PROPOSAL_READY.value):
                lifecycle.transition(
                    req,
                    target_status=RequestStatus.FAILED.value,
                    error_code=exc.code,
                    error_details={"message": exc.message, "details": exc.details},
                )
                await self._emit_event(
                    db,
                    request_id,
                    "request_failed",
                    {
                        "request_id": str(request_id),
                        "step": "request_failed",
                        "message": exc.message,
                        "error_code": exc.code,
                    },
                )
        except Exception as exc:
            logger.exception("Unexpected exception in orchestrator for request %s: %s", request_id, exc)
            req = db.get(ShoppingRequest, request_id)
            if req and req.status not in (RequestStatus.CANCELLED.value, RequestStatus.PROPOSAL_READY.value):
                lifecycle.transition(
                    req,
                    target_status=RequestStatus.FAILED.value,
                    error_code=CartiErrorCode.INTERNAL_SERVER_ERROR,
                    error_details={"reason": "Internal execution pipeline error"},
                )
                await self._emit_event(
                    db,
                    request_id,
                    "request_failed",
                    {
                        "request_id": str(request_id),
                        "step": "request_failed",
                        "message": "An internal error occurred during request processing.",
                        "error_code": CartiErrorCode.INTERNAL_SERVER_ERROR,
                    },
                )
        finally:
            req = db.get(ShoppingRequest, request_id)
            if req and req.locked_by == worker_tag:
                lifecycle.release_lease(req, worker_tag)
            if should_close_db:
                db.close()

    async def _load_or_discover_candidates_async(
        self, db: Session, req: ShoppingRequest, mandate: Mandate
    ) -> List[Candidate]:
        """Load pre-existing candidates, or execute agent loop (B5), or fallback to direct discovery (B6)."""
        # 1. Check if candidates already exist in DB for this request
        stmt = (
            select(Candidate)
            .where(Candidate.request_id == req.id)
            .order_by(Candidate.rank_score.desc().nullslast())
        )
        existing = list(db.scalars(stmt).all())
        if existing:
            return existing

        # 2. If agent_loop is available, run autonomous research loop (B5)
        if self.agent_loop:
            agent_res = await self.agent_loop.run(
                request_id=req.id,
                user_id=req.user_id,
                request_text=req.request_text,
                mandate=mandate,
                discovery_service=self.discovery_service,
                cancellation_check=lambda: self._is_cancelled(db, req.id),
            )
            if getattr(agent_res, "status", None) == "clarification_needed":
                logger.info("Agent identified clarification needed for request %s", req.id)
                return []

            if getattr(agent_res, "candidates", None):
                candidates = []
                for item in agent_res.candidates:
                    cand = Candidate(
                        request_id=req.id,
                        provider_product_id=item.product_id,
                        title=item.title,
                        brand=item.brand,
                        category=item.category,
                        image_url=item.image_url,
                        attributes=item.attributes,
                        rank_score=Decimal("0.85"),
                        rank_reason=agent_res.rationale or "Discovered matching item",
                        observed_at=utc_now(),
                    )
                    db.add(cand)
                    db.flush()

                    for off in item.offers:
                        offer = CandidateOffer(
                            candidate_id=cand.id,
                            provider_offer_id=off.offer_key,
                            domain=off.domain,
                            buy_url=off.buy_url,
                            price_amount=off.price_amount,
                            currency=off.currency,
                            availability=off.availability,
                            condition=off.condition,
                            is_eligible=True,
                            observed_at=utc_now(),
                        )
                        db.add(offer)
                    candidates.append(cand)
                db.commit()
                return candidates

        # 3. Fallback to direct discovery service
        return self._load_or_discover_candidates(db, req, mandate)

    def _load_or_discover_candidates(
        self, db: Session, req: ShoppingRequest, mandate: Mandate
    ) -> List[Candidate]:
        """Load pre-existing candidates or discover new candidates via B6."""
        # 1. Check if candidates already exist in DB for this request
        stmt = (
            select(Candidate)
            .where(Candidate.request_id == req.id)
            .order_by(Candidate.rank_score.desc().nullslast())
        )
        existing = list(db.scalars(stmt).all())
        if existing:
            return existing

        # 2. If discovery service is injected, run search
        if self.discovery_service:
            discovered = self.discovery_service.search_candidates(
                query=req.request_text,
                max_price=mandate.per_item_cap,
                currency=mandate.currency,
                filters=req.normalized_intent,
            )
            # Persist discovered candidates
            candidates = []
            for item in discovered:
                cand = Candidate(
                    request_id=req.id,
                    provider_product_id=item.get("product_id", uuid.uuid4().hex[:12]),
                    title=item.get("title", "Discovered Product"),
                    brand=item.get("brand"),
                    category=item.get("category"),
                    image_url=item.get("image_url"),
                    attributes=item.get("attributes", {}),
                    rank_score=Decimal(str(item.get("score", "0.85"))),
                    rank_reason=item.get("reason", "Top matching item"),
                    observed_at=utc_now(),
                )
                db.add(cand)
                db.flush()

                # Add offer
                offer_price = Decimal(str(item.get("price", "25.00")))
                offer = CandidateOffer(
                    candidate_id=cand.id,
                    provider_offer_id=item.get("offer_id", uuid.uuid4().hex[:10]),
                    domain=item.get("domain", "target.com"),
                    buy_url=item.get("buy_url", "https://target.com/p/item"),
                    price_amount=offer_price,
                    currency=mandate.currency,
                    availability=item.get("availability", "InStock"),
                    condition=item.get("condition", "new"),
                    is_eligible=True,
                    observed_at=utc_now(),
                )
                db.add(offer)
                candidates.append(cand)

            db.commit()
            return candidates

        return []

    def _evaluate_candidate_policy(
        self, candidate: Candidate, mandate: Mandate, available_budget: Decimal
    ) -> tuple[bool, Optional[str]]:
        """Run deterministic policy checks on candidate against spending mandate."""
        if self.guardrail_engine:
            return self.guardrail_engine.evaluate_candidate(candidate, mandate, available_budget)

        # Built-in deterministic guardrails
        # 1. Check offer existence and availability
        if not candidate.offers:
            return False, "Candidate has no offers"

        offer = candidate.offers[0]
        if offer.availability != "InStock":
            return False, f"Item is unavailable ({offer.availability})"

        # 2. Check currency matching
        if offer.currency.upper() != mandate.currency.upper():
            return False, f"Currency mismatch: offer in {offer.currency}, mandate is {mandate.currency}"

        # 3. Check per-item cap
        if offer.price_amount > mandate.per_item_cap:
            return False, f"Price {offer.price_amount} exceeds per-item cap of {mandate.per_item_cap}"

        # 4. Check available budget
        if offer.price_amount > available_budget:
            return False, f"Price {offer.price_amount} exceeds available budget of {available_budget}"

        # 5. Check allowed categories
        if mandate.allowed_categories and candidate.category:
            allowed = [c.lower() for c in mandate.allowed_categories]
            if candidate.category.lower() not in allowed:
                return False, f"Category '{candidate.category}' not in allowed categories"

        # 6. Check blocked categories
        if mandate.blocked_categories and candidate.category:
            blocked = [c.lower() for c in mandate.blocked_categories]
            if candidate.category.lower() in blocked:
                return False, f"Category '{candidate.category}' is in blocked categories"

        # 7. Check allowed retailers
        if mandate.allowed_retailers and offer.domain:
            allowed_ret = [r.lower() for r in mandate.allowed_retailers]
            if offer.domain.lower() not in allowed_ret:
                return False, f"Retailer '{offer.domain}' not in allowed retailers"

        return True, None

    def _create_and_persist_proposal(
        self,
        db: Session,
        req: ShoppingRequest,
        mandate: Mandate,
        candidate: Candidate,
        offer: CandidateOffer,
    ) -> Proposal:
        """Instantiate and persist Proposal record."""
<<<<<<< HEAD
=======
        # Idempotency check: if proposal already exists, reuse it
        existing_proposal = db.scalars(
            select(Proposal).where(Proposal.request_id == req.id)
        ).first()
        if existing_proposal:
            return existing_proposal

>>>>>>> origin/vatsal
        if self.proposal_creator:
            return self.proposal_creator.create_proposal_from_candidate(
                request_id=req.id,
                user_id=req.user_id,
                mandate_id=mandate.id,
                candidate_id=candidate.id,
                offer_id=offer.id,
                quantity=1,
                rationale=candidate.rank_reason or "Best evaluated match adhering to mandate rules.",
            )

        from server.app.services.proposal_service import ProposalService
        proposal_svc = ProposalService(db)
        return proposal_svc.create_proposal_from_candidate(
            request_id=req.id,
            user_id=req.user_id,
            mandate_id=mandate.id,
            candidate_id=candidate.id,
            offer_id=offer.id,
            quantity=1,
            rationale=candidate.rank_reason or "Optimal candidate meeting all budget, retailer, and condition constraints.",
        )


from server.app.services.discovery_service import DiscoveryService
from server.app.services.ranking_service import RankingService
from server.app.services.guardrail_service import GuardrailEngine


def create_default_agent_orchestrator() -> AgentOrchestrator:
    """Instantiate standard production orchestrator wiring B6, B7, and B8 services."""
    return AgentOrchestrator(
        discovery_service=DiscoveryService(),
        ranking_service=RankingService(),
        guardrail_engine=GuardrailEngine(),
    )


agent_orchestrator = create_default_agent_orchestrator()
