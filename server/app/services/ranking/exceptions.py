"""Structured exceptions for Module B7 (Candidate Ranking & Explanation)."""

from typing import Optional


class B7Error(Exception):
    """Base exception for all candidate ranking and explanation errors."""

    def __init__(self, message: str, code: str = "B7_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class RankingConfigurationError(B7Error):
    """Raised when scoring weights or ranking parameters are invalid."""

    def __init__(self, message: str):
        super().__init__(message=message, code="CONFIG_ERROR")


class InvalidInputError(B7Error):
    """Raised when shopping request, mandate snapshot, or candidate options are malformed."""

    def __init__(self, message: str):
        super().__init__(message=message, code="INVALID_INPUT")


class NoEligibleCandidatesError(B7Error):
    """Raised when all candidate offers fail hard eligibility requirements."""

    def __init__(self, message: str = "No candidate options met the eligibility constraints."):
        super().__init__(message=message, code="NO_ELIGIBLE_CANDIDATES")


class ExplanationError(B7Error):
    """Raised when explanation generation encounters a failure or fact-check violation."""

    def __init__(self, message: str):
        super().__init__(message=message, code="EXPLANATION_ERROR")


class StaleDataError(B7Error):
    """Raised when candidate product or offer data violates freshness limits."""

    def __init__(self, message: str):
        super().__init__(message=message, code="STALE_DATA")
