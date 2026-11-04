"""Centralized allowlisted Tool Gateway and Registry (Module B5).

Enforces strict allowlist validation, argument schemas, execution budgets,
timeouts, loop prevention, and privileged operation barriers.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import ValidationError

from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.agent.prompt_defense import PromptDefense
from server.app.agent.schemas import ToolCallRequest, ToolExecutionResult
from server.app.agent.tools import (
    BaseTool,
    CompareCandidatesTool,
    GetProductTool,
    ProposePurchaseTool,
    SearchProductsTool,
    ToolContext,
)

logger = logging.getLogger("carti.agent.gateway")

# Explicit list of forbidden capabilities that must NEVER be exposed or invoked
FORBIDDEN_CAPABILITIES: Set[str] = {
    "create_paypal_order",
    "capture_payment",
    "refund_payment",
    "authorize_payment",
    "execute_checkout",
    "modify_mandate",
    "revoke_mandate",
    "reserve_budget",
    "release_budget",
    "execute_sql",
    "run_query",
    "database_write",
    "execute_shell",
    "run_command",
    "system_exec",
    "fetch_url",
    "arbitrary_http",
    "browser_navigate",
    "authenticate_user",
    "revoke_session",
}


class ToolGateway:
    """Centralized allowlisted gateway executing authorized research tools only."""

    def __init__(
        self,
        max_tool_calls: Optional[int] = None,
        max_search_calls: Optional[int] = None,
        tool_timeout_seconds: Optional[float] = None,
    ):
        self._registry: Dict[str, BaseTool] = {}
        self.max_tool_calls = max_tool_calls or settings.AGENT_MAX_TOOL_CALLS
        self.max_search_calls = max_search_calls or settings.AGENT_MAX_SEARCH_CALLS
        self.tool_timeout_seconds = tool_timeout_seconds or settings.TOOL_DEFAULT_TIMEOUT_SECONDS

        # Register default approved research tools
        self.register_tool(SearchProductsTool())
        self.register_tool(GetProductTool())
        self.register_tool(ProposePurchaseTool())
        self.register_tool(CompareCandidatesTool())

    def register_tool(self, tool: BaseTool) -> None:
        """Register an explicitly approved tool in the gateway."""
        if tool.name in FORBIDDEN_CAPABILITIES:
            raise ValueError(f"Cannot register forbidden capability: {tool.name}")
        self._registry[tool.name] = tool
        logger.info("Registered approved tool: %s", tool.name)

    def is_tool_approved(self, tool_name: str) -> bool:
        """Check if a tool name is registered and approved."""
        return tool_name in self._registry

    def is_tool_forbidden(self, tool_name: str) -> bool:
        """Check if a tool name matches privileged or dangerous actions."""
        return tool_name in FORBIDDEN_CAPABILITIES

    async def execute_tool(
        self,
        call: ToolCallRequest,
        context: ToolContext,
        execution_history: List[ToolExecutionResult],
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> ToolExecutionResult:
        """Validate, guard, and execute an authorized research tool."""
        start_time = time.perf_counter()

        # 1. Cancellation checkpoint
        if cancellation_check and cancellation_check():
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="rejected",
                error="Execution cancelled by user.",
                duration_ms=0.0,
            )

        # 2. Critical Security Barrier: check forbidden tools
        if self.is_tool_forbidden(call.tool_name):
            logger.critical(
                "SECURITY ALERT: Attempted invocation of forbidden tool: %s for request %s",
                call.tool_name,
                context.request_id,
            )
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="rejected",
                error=f"FORBIDDEN_TOOL_ACCESS: Invocation of '{call.tool_name}' is strictly forbidden by Carti security policy.",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 3. Allowlist check: reject unknown tools
        if not self.is_tool_approved(call.tool_name):
            logger.warning("Rejected call to unknown tool: %s", call.tool_name)
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="rejected",
                error=f"UNKNOWN_TOOL: Tool '{call.tool_name}' is not in the approved research tool registry.",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 4. Request-level tool budget enforcement
        successful_calls = [r for r in execution_history if r.status == "success"]
        if len(successful_calls) >= self.max_tool_calls:
            logger.warning("Tool call budget exceeded (%s/%s)", len(successful_calls), self.max_tool_calls)
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="rejected",
                error=f"TOOL_BUDGET_EXCEEDED: Maximum request tool budget of {self.max_tool_calls} calls reached.",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 5. Tool-specific budget enforcement (e.g. search_products)
        if call.tool_name == "search_products":
            search_calls = [r for r in successful_calls if r.tool_name == "search_products"]
            if len(search_calls) >= self.max_search_calls:
                return ToolExecutionResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    status="rejected",
                    error=f"TOOL_BUDGET_EXCEEDED: Maximum product search limit of {self.max_search_calls} calls reached.",
                    duration_ms=(time.perf_counter() - start_time) * 1000,
                )

        # 6. Loop & repeated call detection
        arg_hash = self._compute_args_hash(call.arguments)
        if execution_history:
            last_call = execution_history[-1]
            if last_call.tool_name == call.tool_name and last_call.status == "success":
                # Check if identical arguments were passed
                if getattr(last_call, "_arg_hash", None) == arg_hash:
                    return ToolExecutionResult(
                        call_id=call.call_id,
                        tool_name=call.tool_name,
                        status="rejected",
                        error="Repeated tool call rejected to prevent infinite loop.",
                        duration_ms=(time.perf_counter() - start_time) * 1000,
                    )

        # 7. Strict argument validation against Pydantic schema
        tool = self._registry[call.tool_name]
        try:
            validated_args = tool.input_schema.model_validate(call.arguments).model_dump()
        except ValidationError as val_err:
            logger.warning("Validation error on tool '%s' arguments: %s", call.tool_name, val_err)
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="error",
                error=f"INVALID_ARGUMENTS: {str(val_err)}",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 8. Controlled execution with per-tool timeout
        try:
            result = await asyncio.wait_for(
                tool.execute(validated_args, context),
                timeout=self.tool_timeout_seconds,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            res = ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="success",
                result=result,
                duration_ms=round(elapsed_ms, 2),
            )
            setattr(res, "_arg_hash", arg_hash)
            return res

        except asyncio.TimeoutError:
            logger.error("Tool '%s' timed out after %ss", call.tool_name, self.tool_timeout_seconds)
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="timeout",
                error=f"Tool execution timed out after {self.tool_timeout_seconds} seconds.",
                duration_ms=self.tool_timeout_seconds * 1000,
            )
        except CartiAPIException as exc:
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="error",
                error=f"{exc.code}: {exc.message}",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as exc:
            logger.exception("Unexpected error executing tool '%s': %s", call.tool_name, exc)
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status="error",
                error=f"Tool execution failed: {str(exc)}",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

    @staticmethod
    def _compute_args_hash(arguments: Dict[str, Any]) -> str:
        """Create deterministic MD5 hash of tool arguments for loop detection."""
        try:
            dumped = json.dumps(arguments, sort_keys=True, default=str)
            return hashlib.md5(dumped.encode("utf-8")).hexdigest()
        except Exception:
            return ""


def get_default_tool_gateway() -> ToolGateway:
    """Factory for standard configured ToolGateway."""
    return ToolGateway(
        max_tool_calls=settings.AGENT_MAX_TOOL_CALLS,
        max_search_calls=settings.AGENT_MAX_SEARCH_CALLS,
        tool_timeout_seconds=settings.TOOL_DEFAULT_TIMEOUT_SECONDS,
    )
