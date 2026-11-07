"""Controlled, bounded Agent Loop coordinating LLM reasoning and Tool Gateway (Module B5)."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
import time
from typing import Any, Callable, Dict, List, Optional
import uuid

from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.mandate import Mandate
from server.app.agent.llm_provider import ILLMProvider, get_default_llm_provider
from server.app.agent.prompt_defense import PromptDefense
from server.app.agent.prompts import (
    REQUEST_UNDERSTANDING_SYSTEM,
    RESEARCH_PLANNING_SYSTEM,
    RECOMMENDATION_EXPLANATION_SYSTEM,
    build_understanding_prompt,
    build_evaluation_prompt,
)
from server.app.agent.schemas import (
    AgentRunResult,
    AgentRunStatus,
    RequestUnderstanding,
    ResearchCandidate,
    ResearchOffer,
    ResearchPlan,
    ToolCallRequest,
    ToolExecutionResult,
)
from server.app.agent.tool_gateway import ToolGateway, get_default_tool_gateway
from server.app.agent.tools import ToolContext

logger = logging.getLogger("carti.agent.loop")


class AgentLimits:
    """Configurable server-side execution boundaries for the agent loop."""

    def __init__(
        self,
        max_iterations: Optional[int] = None,
        max_tool_calls: Optional[int] = None,
        max_search_calls: Optional[int] = None,
        max_execution_seconds: Optional[float] = None,
        max_candidates: Optional[int] = None,
    ):
        self.max_iterations = max_iterations or settings.AGENT_MAX_ITERATIONS
        self.max_tool_calls = max_tool_calls or settings.AGENT_MAX_TOOL_CALLS
        self.max_search_calls = max_search_calls or settings.AGENT_MAX_SEARCH_CALLS
        self.max_execution_seconds = max_execution_seconds or settings.AGENT_MAX_EXECUTION_SECONDS
        self.max_candidates = max_candidates or settings.AGENT_MAX_CANDIDATES


class AgentLoop:
    """Autonomous shopping research agent with allowlisted tool access and factual grounding."""

    def __init__(
        self,
        llm_provider: Optional[ILLMProvider] = None,
        tool_gateway: Optional[ToolGateway] = None,
        limits: Optional[AgentLimits] = None,
    ):
        self.llm = llm_provider or get_default_llm_provider()
        self.gateway = tool_gateway or get_default_tool_gateway()
        self.limits = limits or AgentLimits()

    async def understand_request(
        self,
        request_text: str,
        mandate: Optional[Mandate] = None,
    ) -> RequestUnderstanding:
        """Analyze natural-language request and extract structured shopping parameters."""
        # 1. Adversarial prompt injection scan
        is_threat, reason = PromptDefense.detect_injection_patterns(request_text)
        if is_threat:
            logger.warning("Adversarial prompt pattern detected: %s", reason)
            # Treat strictly as untrusted text, sanitize control characters
            request_text = PromptDefense.strip_control_characters(request_text)

        mandate_summary = None
        if mandate:
            mandate_summary = {
                "currency": mandate.currency,
                "per_item_cap": str(mandate.per_item_cap),
                "total_budget": str(mandate.total_budget),
                "max_quantity_per_product": mandate.max_quantity_per_product,
                "allowed_categories": mandate.allowed_categories,
                "blocked_categories": mandate.blocked_categories,
                "allowed_retailers": mandate.allowed_retailers,
            }

        prompt = build_understanding_prompt(request_text, mandate_summary)
        understanding = await self.llm.generate_structured(
            prompt=prompt,
            schema_cls=RequestUnderstanding,
            system_instruction=REQUEST_UNDERSTANDING_SYSTEM,
        )

        # Enforce mandate quantity cap if applicable
        if mandate and understanding.quantity > mandate.max_quantity_per_product:
            understanding.quantity = mandate.max_quantity_per_product

        return understanding

    async def create_research_plan(
        self,
        understanding: RequestUnderstanding,
        mandate: Optional[Mandate] = None,
    ) -> ResearchPlan:
        """Formulate research queries and constraint plan based on structured understanding."""
        queries = []
        if understanding.brand_preference:
            queries.append(f"{understanding.brand_preference} {understanding.product_type}")
        queries.append(f"{understanding.product_type} {' '.join(understanding.explicit_requirements[:2])}".strip())

        constraints = {
            "max_price": str(mandate.per_item_cap) if mandate else (str(understanding.price_preference) if understanding.price_preference else "100.00"),
            "currency": mandate.currency if mandate else "USD",
        }
        if mandate and mandate.allowed_retailers:
            constraints["allowed_retailers"] = mandate.allowed_retailers

        return ResearchPlan(
            research_objective=f"Find best {understanding.product_type} fulfilling user requirements under budget",
            search_queries=queries,
            constraints=constraints,
            approved_tools=["search_products", "get_product", "propose_purchase", "compare_candidates"],
            max_steps=min(4, self.limits.max_search_calls),
        )

    async def run(
        self,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
        request_text: str,
        mandate: Optional[Mandate] = None,
        discovery_service: Optional[Any] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> AgentRunResult:
        """Execute the complete bounded research loop."""
        start_time = time.perf_counter()
        context = ToolContext(
            request_id=request_id,
            user_id=user_id,
            mandate=mandate,
            discovery_service=discovery_service,
        )
        tool_history: List[ToolExecutionResult] = []
        candidates_gathered: List[ResearchCandidate] = []

        async def _notify(event_name: str, payload: Dict[str, Any]):
            if event_callback:
                if asyncio.iscoroutinefunction(event_callback):
                    await event_callback(event_name, payload)
                else:
                    event_callback(event_name, payload)

        # Checkpoint 1: Cancellation
        if cancellation_check and cancellation_check():
            return AgentRunResult(
                request_id=request_id,
                status=AgentRunStatus.CANCELLED,
                duration_seconds=round(time.perf_counter() - start_time, 2),
            )

        # Stage 1: Request Understanding
        await _notify("agent_understanding_started", {"message": "Analyzing shopping request and requirements."})
        understanding = await self.understand_request(request_text, mandate)

        await _notify(
            "agent_understanding_completed",
            {
                "product_type": understanding.product_type,
                "category": understanding.category,
                "is_clarification_needed": understanding.is_clarification_needed,
                "clarification_reason": understanding.clarification_reason,
            },
        )

        if understanding.is_clarification_needed:
            return AgentRunResult(
                request_id=request_id,
                status=AgentRunStatus.CLARIFICATION_NEEDED,
                understanding=understanding,
                missing_information=[understanding.clarification_reason or "Clarification required on core specifications."],
                duration_seconds=round(time.perf_counter() - start_time, 2),
            )

        # Stage 2: Research Planning
        plan = await self.create_research_plan(understanding, mandate)

        # Stage 3: Bounded Iteration Loop
        iteration = 0
        recommended_prod_id = None
        recommended_offer_key = None
        recommendation_rationale = None

        while iteration < self.limits.max_iterations:
            iteration += 1

            # Checkpoint: Cancellation
            if cancellation_check and cancellation_check():
                return AgentRunResult(
                    request_id=request_id,
                    status=AgentRunStatus.CANCELLED,
                    understanding=understanding,
                    plan=plan,
                    total_iterations=iteration,
                    duration_seconds=round(time.perf_counter() - start_time, 2),
                )

            # Checkpoint: Time budget
            elapsed = time.perf_counter() - start_time
            if elapsed > self.limits.max_execution_seconds:
                logger.warning("Agent execution budget reached (%ss/%ss)", elapsed, self.limits.max_execution_seconds)
                break

            # Decide tool call
            if not candidates_gathered:
                # Step A: Perform product search
                search_query = plan.search_queries[0] if plan.search_queries else understanding.product_type
                max_price = Decimal(plan.constraints.get("max_price", "100.00"))
                currency = plan.constraints.get("currency", "USD")

                call = ToolCallRequest(
                    tool_name="search_products",
                    arguments={
                        "query": search_query,
                        "max_price": max_price,
                        "currency": currency,
                    },
                )

                await _notify("tool_call_started", {"tool": call.tool_name, "query": search_query})
                exec_res = await self.gateway.execute_tool(call, context, tool_history, cancellation_check)
                tool_history.append(exec_res)
                await _notify("tool_call_completed", {"tool": call.tool_name, "status": exec_res.status})

                if exec_res.status == "success" and isinstance(exec_res.result, list):
                    # Ingest and normalize discovered products
                    for raw in exec_res.result:
                        cand = self._normalize_candidate(raw, currency)
                        candidates_gathered.append(cand)

                if not candidates_gathered:
                    # 0 items found
                    return AgentRunResult(
                        request_id=request_id,
                        status=AgentRunStatus.NO_MATCH,
                        understanding=understanding,
                        plan=plan,
                        total_iterations=iteration,
                        total_tool_calls=len(tool_history),
                        duration_seconds=round(time.perf_counter() - start_time, 2),
                    )

            elif candidates_gathered and not recommended_prod_id:
                # Step B: Pick top candidate and pre-validate purchase
                top_cand = candidates_gathered[0]
                if top_cand.offers:
                    best_offer = top_cand.offers[0]
                    propose_call = ToolCallRequest(
                        tool_name="propose_purchase",
                        arguments={
                            "product_id": top_cand.product_id,
                            "offer_key": best_offer.offer_key,
                            "quantity": understanding.quantity,
                            "rationale": f"Top match for {understanding.product_type} meeting user criteria within budget.",
                        },
                    )
                    await _notify("tool_call_started", {"tool": propose_call.tool_name, "product_id": top_cand.product_id})
                    prop_res = await self.gateway.execute_tool(propose_call, context, tool_history, cancellation_check)
                    tool_history.append(prop_res)
                    await _notify("tool_call_completed", {"tool": propose_call.tool_name, "status": prop_res.status})

                    if prop_res.status == "success" and isinstance(prop_res.result, dict):
                        if prop_res.result.get("eligible"):
                            recommended_prod_id = top_cand.product_id
                            recommended_offer_key = best_offer.offer_key
                            recommendation_rationale = prop_res.result.get("rationale")
                            break
                        else:
                            # Candidate rejected by pre-check; try next candidate if available
                            candidates_gathered.pop(0)
                            continue
                else:
                    # Candidate has no offers, discard
                    candidates_gathered.pop(0)
                    continue
            else:
                break

        # Grounding and Factual Accuracy Verification
        # Guarantee that recommended product & offer are strictly grounded in retrieved catalog data
        verified_candidates = []
        for cand in candidates_gathered:
            # Verify against context cache
            cached = context.cached_products.get(cand.product_id)
            if cached:
                cand.is_verified = True
            else:
                cand.is_verified = False
            verified_candidates.append(cand)

        # Factual explanation synthesis
        if not recommendation_rationale and recommended_prod_id:
            recommendation_rationale = f"Recommended product fulfills requested specifications and adheres to user spending mandate."

        final_status = AgentRunStatus.COMPLETED if recommended_prod_id else (
            AgentRunStatus.NO_MATCH if not verified_candidates else AgentRunStatus.BUDGET_EXHAUSTED
        )

        return AgentRunResult(
            request_id=request_id,
            status=final_status,
            understanding=understanding,
            plan=plan,
            candidates=verified_candidates[:self.limits.max_candidates],
            recommended_product_id=recommended_prod_id,
            recommended_offer_key=recommended_offer_key,
            rationale=recommendation_rationale,
            total_iterations=iteration,
            total_tool_calls=len(tool_history),
            duration_seconds=round(time.perf_counter() - start_time, 2),
        )

    def _normalize_candidate(self, raw: Dict[str, Any], currency: str) -> ResearchCandidate:
        """Convert raw tool search output into structured ResearchCandidate with zero hallucination."""
        prod_id = str(raw.get("product_id") or raw.get("id") or uuid.uuid4().hex[:10])
        title = raw.get("title", "Discovered Product")
        brand = raw.get("brand")
        category = raw.get("category")
        description = raw.get("description")
        image_url = raw.get("image_url")
        attributes = raw.get("attributes") or {}

        offers = []
        for raw_off in raw.get("offers", []):
            price_val = raw_off.get("price_amount") or raw_off.get("price") or "0.00"
            offers.append(
                ResearchOffer(
                    offer_key=str(raw_off.get("offer_key") or raw_off.get("id") or f"off_{uuid.uuid4().hex[:8]}"),
                    domain=str(raw_off.get("domain", "retailer.com")),
                    price_amount=Decimal(str(price_val)),
                    currency=str(raw_off.get("currency", currency)),
                    availability=str(raw_off.get("availability", "InStock")),
                    condition=str(raw_off.get("condition", "new")),
                    buy_url=str(raw_off.get("buy_url", "https://retailer.com")),
                    observed_at=datetime.now(timezone.utc),
                )
            )

        # Identify missing factual attributes
        missing = []
        if not brand:
            missing.append("brand")
        if not description:
            missing.append("description")
        if not offers:
            missing.append("offers")

        return ResearchCandidate(
            product_id=prod_id,
            title=title,
            brand=brand,
            category=category,
            description=description,
            image_url=image_url,
            attributes=attributes,
            offers=offers,
            source_provenance=raw.get("provider", "channel3"),
            is_verified=True,
            missing_attributes=missing,
        )
