"""Abstract interfaces for Module B7 (Candidate Ranking & Explanation)."""

from abc import ABC, abstractmethod
from typing import Optional
from server.app.services.ranking.models import (
    CandidateOption,
    ComparisonResult,
    MandateSnapshot,
    RankedCandidate,
    RejectionDetail,
    ShoppingRequest,
)


class IEligibilityFilter(ABC):
    """Contract for deterministic pre-filtering of candidate options."""

    @abstractmethod
    def evaluate(
        self,
        candidate: CandidateOption,
        request: ShoppingRequest,
        mandate: Optional[MandateSnapshot] = None,
    ) -> list[RejectionDetail]:
        """Evaluate a candidate option against request and mandate constraints.

        Returns:
            List of RejectionDetail reasons if ineligible, or empty list if eligible.
        """
        ...


class ICandidateScorer(ABC):
    """Contract for calculating normalized ranking scores."""

    @abstractmethod
    def score_candidate(
        self,
        candidate: CandidateOption,
        request: ShoppingRequest,
        mandate: Optional[MandateSnapshot] = None,
    ) -> tuple[float, dict[str, float], list[str], list[str]]:
        """Compute score, score breakdown, positive matching factors, and uncertain data.

        Returns:
            Tuple of (ranking_score, score_breakdown, positive_factors, missing_info).
        """
        ...


class IRankingService(ABC):
    """Contract for ranking eligible candidates deterministically."""

    @abstractmethod
    def rank_candidates(
        self,
        eligible_candidates: list[CandidateOption],
        request: ShoppingRequest,
        mandate: Optional[MandateSnapshot] = None,
    ) -> list[RankedCandidate]:
        """Score, sort, and position-rank eligible candidates."""
        ...


class IExplanationGenerator(ABC):
    """Contract for generating grounded explanations for recommendations and exclusions."""

    @abstractmethod
    def generate_explanation(
        self,
        request: ShoppingRequest,
        ranked_candidates: list[RankedCandidate],
        rejected_candidates: list[RankedCandidate],
    ) -> str:
        """Produce a concise, factual explanation grounded strictly in candidate data."""
        ...


class ILLMExplanationAdapter(ABC):
    """Optional contract for LLM-assisted explanation draft generation with safe fallback."""

    @abstractmethod
    async def draft_explanation(
        self,
        facts: dict[str, object],
    ) -> Optional[str]:
        """Draft natural-language text from validated facts without payment access."""
        ...


class IComparisonService(ABC):
    """Contract for orchestrating end-to-end candidate comparison."""

    @abstractmethod
    def compare_and_rank(
        self,
        request: ShoppingRequest,
        candidates: list[CandidateOption],
        mandate: Optional[MandateSnapshot] = None,
    ) -> ComparisonResult:
        """Filter, rank, and explain candidate options."""
        ...
