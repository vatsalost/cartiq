"""High-level comparison service coordinating filtering, ranking, and explanation."""

from datetime import datetime, timezone
import logging
from typing import Any, Optional, Union
from modules.b7_candidate_ranking.config import RankingConfig
from modules.b7_candidate_ranking.eligibility import EligibilityFilter
from modules.b7_candidate_ranking.explanation_service import ExplanationService
from modules.b7_candidate_ranking.interfaces import IComparisonService
from modules.b7_candidate_ranking.models import (
    CandidateOffer,
    CandidateOption,
    CandidateProduct,
    ComparisonResult,
    EligibilityStatus,
    MandateSnapshot,
    RankedCandidate,
    ShoppingRequest,
)
from modules.b7_candidate_ranking.ranking_service import RankingService

logger = logging.getLogger("cartiq.ranking.comparison")


class ComparisonService(IComparisonService):
    """Coordinates deterministic pre-filtering, transparent scoring, and factual explanation."""

    def __init__(
        self,
        config: Optional[RankingConfig] = None,
        eligibility_filter: Optional[EligibilityFilter] = None,
        ranking_service: Optional[RankingService] = None,
        explanation_service: Optional[ExplanationService] = None,
    ):
        self.config = config or RankingConfig()
        self.eligibility_filter = eligibility_filter or EligibilityFilter(config=self.config)
        self.ranking_service = ranking_service or RankingService(config=self.config)
        self.explanation_service = explanation_service or ExplanationService(config=self.config)

    @staticmethod
    def adapt_b6_product(b6_product: Any) -> list[CandidateOption]:
        """Convert a B6 NormalizedProduct into discrete B7 CandidateOption instances."""
        options: list[CandidateOption] = []

        prod = CandidateProduct(
            product_id=str(getattr(b6_product, "product_id", "")),
            title=str(getattr(b6_product, "title", "")),
            brand=getattr(b6_product, "brand", None),
            category=getattr(b6_product, "category", None),
            description=getattr(b6_product, "description", None),
            attributes=getattr(b6_product, "attributes", {}) or {},
            variants=getattr(b6_product, "variants", []) or [],
            image_url=getattr(b6_product, "image_url", None),
            observed_at=getattr(b6_product, "observed_at", datetime.now(timezone.utc)),
        )

        offers = getattr(b6_product, "offers", []) or []
        for raw_off in offers:
            cand_off = CandidateOffer(
                offer_key=str(getattr(raw_off, "offer_key", "")),
                domain=str(getattr(raw_off, "domain", "")),
                buy_url=str(getattr(raw_off, "buy_url", "")),
                price_amount=getattr(raw_off, "price_amount", None),
                currency=str(getattr(raw_off, "currency", "USD")),
                availability=str(getattr(raw_off, "availability", "Unknown")),
                condition=str(getattr(raw_off, "condition", "new")),
                observed_at=getattr(raw_off, "observed_at", datetime.now(timezone.utc)),
            )
            options.append(CandidateOption.create(product=prod, offer=cand_off))

        return options

    def filter_candidates(
        self,
        request: ShoppingRequest,
        candidates: list[CandidateOption],
        mandate: Optional[MandateSnapshot] = None,
    ) -> tuple[list[CandidateOption], list[RankedCandidate]]:
        """Separate candidate options into eligible and rejected subsets."""
        eligible: list[CandidateOption] = []
        rejected: list[RankedCandidate] = []

        for candidate in candidates:
            rejections = self.eligibility_filter.evaluate(
                candidate=candidate,
                request=request,
                mandate=mandate,
            )

            if not rejections:
                eligible.append(candidate)
            else:
                rejected_item = RankedCandidate(
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
                    eligibility_status=EligibilityStatus.INELIGIBLE,
                    ranking_score=0.0,
                    score_breakdown={},
                    positive_matching_factors=[],
                    missing_or_uncertain_information=[],
                    rejection_reasons=rejections,
                )
                rejected.append(rejected_item)

        return eligible, rejected

    def compare_and_rank(
        self,
        request: ShoppingRequest,
        candidates: list[CandidateOption],
        mandate: Optional[MandateSnapshot] = None,
    ) -> ComparisonResult:
        """Execute end-to-end evaluation: pre-filtering, scoring, ranking, and explanation."""
        logger.info("Evaluating %d candidate options for request", len(candidates))

        # 1. Deterministic Pre-Filtering
        eligible_options, rejected_candidates = self.filter_candidates(
            request=request,
            candidates=candidates,
            mandate=mandate,
        )

        # 2. Ranking Eligible Candidates
        ranked_candidates = self.ranking_service.rank_candidates(
            eligible_candidates=eligible_options,
            request=request,
            mandate=mandate,
        )

        selected = ranked_candidates[0] if ranked_candidates else None

        # 3. Generating Factual Explanation
        explanation = self.explanation_service.generate_explanation(
            request=request,
            ranked_candidates=ranked_candidates,
            rejected_candidates=rejected_candidates,
        )

        # 4. Aggregating missing/uncertain data points
        missing_data: list[str] = []
        for r in ranked_candidates:
            missing_data.extend(r.missing_or_uncertain_information)

        return ComparisonResult(
            ranked_candidates=ranked_candidates,
            rejected_candidates=rejected_candidates,
            selected_candidate=selected,
            score_breakdown=selected.score_breakdown if selected else {},
            explanation=explanation,
            missing_or_uncertain_data=list(set(missing_data)),
            evaluation_timestamp=datetime.now(timezone.utc),
        )

    def get_rejected_alternatives(self, comparison_result: ComparisonResult) -> list[RankedCandidate]:
        """Convenience accessor to retrieve all rejected candidates with reasons."""
        return comparison_result.rejected_candidates
