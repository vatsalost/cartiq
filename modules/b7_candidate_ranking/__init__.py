"""Module B7 — Candidate Ranking and Explanation Service.

Transforms raw candidate options into a transparent, ranked comparison list
with deterministic pre-filtering and fact-grounded explanations.
"""

from modules.b7_candidate_ranking.comparison_service import ComparisonService
from modules.b7_candidate_ranking.config import RankingConfig, ScoringWeights
from modules.b7_candidate_ranking.eligibility import EligibilityFilter
from modules.b7_candidate_ranking.exceptions import (
    B7Error,
    ExplanationError,
    InvalidInputError,
    NoEligibleCandidatesError,
    RankingConfigurationError,
    StaleDataError,
)
from modules.b7_candidate_ranking.explanation_service import ExplanationService
from modules.b7_candidate_ranking.interfaces import (
    ICandidateScorer,
    IComparisonService,
    IEligibilityFilter,
    IExplanationGenerator,
    ILLMExplanationAdapter,
    IRankingService,
)
from modules.b7_candidate_ranking.models import (
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
from modules.b7_candidate_ranking.ranking_service import RankingService
from modules.b7_candidate_ranking.scoring import CandidateScorer

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
