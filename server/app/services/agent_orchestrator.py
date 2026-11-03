"""Agent orchestrator interface and task runner."""

import asyncio
import logging
from typing import Dict, Optional
import uuid
from sqlalchemy.orm import Session
from server.app.db.session import SessionLocal
from server.app.models.request import ShoppingRequest, RequestEvent
from server.app.schemas.request import RequestEventResponse
from server.app.services.event_bus import event_bus

logger = logging.getLogger("carti.agent")


class AgentOrchestrator:
    """Orchestrates background search and candidate evaluation for shopping requests."""

    def __init__(self):
        self._active_tasks: Dict[uuid.UUID, asyncio.Task] = {}

    def start_request_run(self, request_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Schedule agent loop in background task."""
        # Cancel any existing task for this request
        if request_id in self._active_tasks:
            self._active_tasks[request_id].cancel()

        task = asyncio.create_task(self._run_agent_lifecycle(request_id, user_id))
        self._active_tasks[request_id] = task

        def _cleanup(t):
            self._active_tasks.pop(request_id, None)

        task.add_done_callback(_cleanup)

    def stop_request_run(self, request_id: uuid.UUID) -> None:
        """Cancel an in-progress agent run."""
        task = self._active_tasks.pop(request_id, None)
        if task and not task.done():
            task.cancel()
            logger.info("Cancelled agent task for request: %s", request_id)

    async def _emit_event(
        self, db: Session, request_id: uuid.UUID, event_type: str, payload: dict
    ) -> RequestEvent:
        """Persist event to database then broadcast to live SSE listeners."""
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

    async def _run_agent_lifecycle(self, request_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Background execution lifecycle for request processing."""
        db: Session = SessionLocal()
        try:
            req = db.get(ShoppingRequest, request_id)
            if not req or req.status == "cancelled":
                return

            req.status = "running"
            db.commit()

            # Emit initial orchestration events
            await self._emit_event(
                db,
                request_id,
                "search_started",
                {
                    "request_id": str(request_id),
                    "step": "search_started",
                    "message": "Initiating product search across authorized retailers.",
                    "progress": 20,
                },
            )

            # Check for cancellation
            await asyncio.sleep(0.5)
            db.refresh(req)
            if req.status == "cancelled":
                return

            await self._emit_event(
                db,
                request_id,
                "search_results_received",
                {
                    "request_id": str(request_id),
                    "step": "search_results_received",
                    "message": "Retrieved candidate product offers for evaluation.",
                    "progress": 50,
                },
            )

        except asyncio.CancelledError:
            logger.info("Agent run cancelled for request: %s", request_id)
        except Exception as exc:
            logger.exception("Error during agent run for request %s: %s", request_id, exc)
            req = db.get(ShoppingRequest, request_id)
            if req and req.status != "cancelled":
                req.status = "failed"
                req.error_code = "AGENT_EXECUTION_ERROR"
                db.commit()
                await self._emit_event(
                    db,
                    request_id,
                    "request_failed",
                    {
                        "request_id": str(request_id),
                        "step": "request_failed",
                        "message": "Shopping search encountered an error.",
                        "error_code": "AGENT_EXECUTION_ERROR",
                    },
                )
        finally:
            db.close()


agent_orchestrator = AgentOrchestrator()
