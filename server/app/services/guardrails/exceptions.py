"""Structured exceptions for Module B8 (Deterministic Guardrail & Policy Engine)."""


class B8Error(Exception):
    """Base exception for all guardrail and policy engine errors."""

    def __init__(self, message: str, code: str = "B8_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class InvalidInputError(B8Error):
    """Raised when mandate snapshot, candidate, or offer data is structurally invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message=message, code="INVALID_INPUT")


class MandateMissingError(B8Error):
    """Raised when no mandate is present but one is required for policy evaluation."""

    def __init__(self, message: str = "No active mandate available for policy evaluation."):
        super().__init__(message=message, code="MANDATE_MISSING")


class MandateExpiredError(B8Error):
    """Raised when the mandate's expiration timestamp has elapsed."""

    def __init__(self, message: str = "The active mandate has expired."):
        super().__init__(message=message, code="MANDATE_EXPIRED")


class MandateInvalidError(B8Error):
    """Raised when the mandate is in an invalid or non-active lifecycle state (e.g. revoked, superseded)."""

    def __init__(self, message: str = "The mandate is in an invalid or inactive state."):
        super().__init__(message=message, code="MANDATE_INVALID")


class PolicyEvaluationError(B8Error):
    """Raised when the policy engine encounters an unrecoverable internal evaluation error."""

    def __init__(self, message: str):
        super().__init__(message=message, code="POLICY_EVALUATION_ERROR")
