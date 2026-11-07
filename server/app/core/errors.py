"""Centralized error handling and Carti API exceptions."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class CartiErrorCode:
    """Standardized error codes for Carti API."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    ACCESS_DENIED = "ACCESS_DENIED"
    MANDATE_NOT_FOUND = "MANDATE_NOT_FOUND"
    MANDATE_EXPIRED = "MANDATE_EXPIRED"
    MANDATE_INVALID = "MANDATE_INVALID"
    REQUEST_NOT_FOUND = "REQUEST_NOT_FOUND"
    REQUEST_ALREADY_COMPLETED = "REQUEST_ALREADY_COMPLETED"
    REQUEST_CANCELLED = "REQUEST_CANCELLED"
    NO_ELIGIBLE_PRODUCTS = "NO_ELIGIBLE_PRODUCTS"
    PROPOSAL_NOT_FOUND = "PROPOSAL_NOT_FOUND"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    PROPOSAL_STALE = "PROPOSAL_STALE"
    OFFER_PRICE_CHANGED = "OFFER_PRICE_CHANGED"
    OFFER_UNAVAILABLE = "OFFER_UNAVAILABLE"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    PAYPAL_ORDER_FAILED = "PAYPAL_ORDER_FAILED"
    PAYMENT_CAPTURE_FAILED = "PAYMENT_CAPTURE_FAILED"
    REFUND_NOT_ALLOWED = "REFUND_NOT_ALLOWED"
    WEBHOOK_SIGNATURE_INVALID = "WEBHOOK_SIGNATURE_INVALID"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    REQUEST_EXECUTION_LOCKED = "REQUEST_EXECUTION_LOCKED"
    RETRY_LIMIT_EXCEEDED = "RETRY_LIMIT_EXCEEDED"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    DOWNSTREAM_SERVICE_UNAVAILABLE = "DOWNSTREAM_SERVICE_UNAVAILABLE"
    GUARDRAIL_BLOCKED = "GUARDRAIL_BLOCKED"
    GUARDRAIL_VIOLATION = "GUARDRAIL_BLOCKED"
    PROPOSAL_EXPIRED = "PROPOSAL_EXPIRED"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    FORBIDDEN_TOOL_ACCESS = "FORBIDDEN_TOOL_ACCESS"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_BUDGET_EXCEEDED = "TOOL_BUDGET_EXCEEDED"
    LLM_PROVIDER_ERROR = "LLM_PROVIDER_ERROR"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class CartiAPIException(Exception):
    """Base application exception returning structured Carti error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
                "details": self.details,
            }
        }


def format_error_response(
    code: str,
    message: str,
    status_code: int,
    retryable: bool = False,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Format standard JSONResponse with Carti error structure."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "details": details or {},
            }
        },
    )


async def carti_exception_handler(request: Request, exc: CartiAPIException) -> JSONResponse:
    """FastAPI handler for custom Carti exceptions."""
    return format_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        retryable=exc.retryable,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI handler for Pydantic RequestValidationError."""
    errors_summary = []
    for error in exc.errors():
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        errors_summary.append({
            "field": loc,
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "value_error"),
        })

    return format_error_response(
        code=CartiErrorCode.VALIDATION_ERROR,
        message="Request payload validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT if hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT") else 422,
        retryable=False,
        details={"validation_errors": errors_summary},
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """FastAPI handler for generic Starlette/FastAPI HTTPExceptions."""
    code_map = {
        status.HTTP_401_UNAUTHORIZED: CartiErrorCode.AUTHENTICATION_REQUIRED,
        status.HTTP_403_FORBIDDEN: CartiErrorCode.ACCESS_DENIED,
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_429_TOO_MANY_REQUESTS: CartiErrorCode.RATE_LIMIT_EXCEEDED,
    }
    code = code_map.get(exc.status_code, CartiErrorCode.INTERNAL_SERVER_ERROR)
    return format_error_response(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code,
        retryable=False,
        details={},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI handler for unhandled exceptions (redacts secrets & stack traces)."""
    return format_error_response(
        code=CartiErrorCode.INTERNAL_SERVER_ERROR,
        message="An unexpected server error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        retryable=True,
        details={},
    )
