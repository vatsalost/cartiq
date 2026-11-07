"""Module B7 — Candidate Ranking and Explanation Service.

Transforms raw candidate options into a transparent, ranked comparison list
with deterministic pre-filtering and fact-grounded explanations.
"""

from server.app.services.ranking.comparison_service import ComparisonService
from server.app.services.ranking.config import RankingConfig, ScoringWeights
from server.app.services.ranking.eligibility import EligibilityFilter
from server.app.services.ranking.exceptions import (
    B7Error,
    ExplanationError,
    InvalidInputError,
    NoEligibleCandidatesError,
    RankingConfigurationError,
    StaleDataError,
)
from server.app.services.ranking.explanation_service import ExplanationService
from server.app.services.ranking.interfaces import (
    ICandidateScorer,
    IComparisonService,
    IEligibilityFilter,
    IExplanationGenerator,
    ILLMExplanationAdapter,
    IRankingService,
)
from server.app.services.ranking.models import (
    CandidateOffer,
    CandidateOption,
    CandidateProduct,
    ComparisonResult,
    EligibilityStatus,
    MandateSnapshot,
    RankedCandidate,
    RejectionCode,
    RejectionDetail,
    ShoppingRequest,
)
from server.app.services.ranking.ranking_service import RankingService
from server.app.services.ranking.scoring import CandidateScorer

__all__ = [
    # Config
    "RankingConfig",
    "ScoringWeights",
    # Models & Enums
    "CandidateOffer",
    "CandidateOption",
    "CandidateProduct",
    "ComparisonResult",
    "EligibilityStatus",
    "MandateSnapshot",
    "RankedCandidate",
    "RejectionCode",
    "RejectionDetail",
    "ShoppingRequest",
    # Services
    "CandidateScorer",
    "ComparisonService",
    "EligibilityFilter",
    "ExplanationService",
    "RankingService",
    # Interfaces
    "ICandidateScorer",
    "IComparisonService",
    "IEligibilityFilter",
    "IExplanationGenerator",
    "ILLMExplanationAdapter",
    "IRankingService",
    # Exceptions
    "B7Error",
    "ExplanationError",
    "InvalidInputError",
    "NoEligibleCandidatesError",
    "RankingConfigurationError",
    "StaleDataError",
]
