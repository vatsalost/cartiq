"""Deterministic ranking service with transparent tie-breaking."""

from typing import Optional
from modules.b7_candidate_ranking.config import RankingConfig
from modules.b7_candidate_ranking.interfaces import IRankingService
from modules.b7_candidate_ranking.models import (
    CandidateOption,
    EligibilityStatus,
    MandateSnapshot,
    RankedCandidate,
    ShoppingRequest,
)
from modules.b7_candidate_ranking.scoring import CandidateScorer


class RankingService(IRankingService):
    """Orders eligible candidates deterministically using normalized scores and tie-breakers."""

    def __init__(
        self,
        config: Optional[RankingConfig] = None,
        scorer: Optional[CandidateScorer] = None,
    ):
        self.config = config or RankingConfig()
        self.scorer = scorer or CandidateScorer(config=self.config)

    def rank_candidates(
        self,
        eligible_candidates: list[CandidateOption],
        request: ShoppingRequest,
        mandate: Optional[MandateSnapshot] = None,
    ) -> list[RankedCandidate]:
        """Score and sort eligible candidates.

        Tie-breaking order:
        1. Ranking score (descending)
        2. Offer price (ascending - lower price breaks score ties)
        3. Number of positive matching factors (descending)
        4. Alphabetical by candidate_id (product_id:offer_key) for absolute determinism.
        """
        evaluated: list[RankedCandidate] = []

        for candidate in eligible_candidates:
            score, breakdown, positive_factors, uncertain_info = self.scorer.score_candidate(
                candidate=candidate,
                request=request,
                mandate=mandate,
            )

            ranked = RankedCandidate(
                candidate_id=candidate.candidate_id,
                product_id=candidate.product.product_id,
                offer_key=candidate.offer.offer_key,
                product_title=candidate.product.title,
                brand=candidate.product.brand,
                category=candidate.product.category,
                domain=candidate.offer.domain,
                price_amount=candidate.offer.price_amount,
                currency=candidate.offer.currency,
                availability=candidate.offer.availability,
                condition=candidate.offer.condition,
                buy_url=candidate.offer.buy_url,
                image_url=candidate.product.image_url,
                attributes=candidate.product.attributes,
                eligibility_status=EligibilityStatus.ELIGIBLE,
                ranking_score=score,
                score_breakdown=breakdown,
                positive_matching_factors=positive_factors,
                missing_or_uncertain_information=uncertain_info,
                rejection_reasons=[],
            )
            evaluated.append(ranked)

        # Deterministic sorting
        # Note: In python sort, ascending key is default.
        # We want: score desc (-score), price asc (price), positive_factors desc (-len), id asc (id)
        def sort_key(item: RankedCandidate):
            return (
                -item.ranking_score,
                item.price_amount,
                -len(item.positive_matching_factors),
                item.candidate_id,
            )

        sorted_candidates = sorted(evaluated, key=sort_key)

        # Assign 1-based ranking position
        for idx, candidate in enumerate(sorted_candidates, start=1):
            candidate.ranking_position = idx

        return sorted_candidates
