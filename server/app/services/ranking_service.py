"""Ranking Service (B7) implementing IRankingService protocol for candidate ranking and scoring."""

from decimal import Decimal
import logging
from typing import List, Optional

from server.app.models.candidate import Candidate
from server.app.models.mandate import Mandate
from server.app.services.interfaces import IRankingService
from server.app.services.ranking.comparison_service import ComparisonService
from server.app.services.ranking.config import RankingConfig
from server.app.services.ranking.models import (
    CandidateOffer,
    CandidateOption,
    CandidateProduct,
    MandateSnapshot,
    ShoppingRequest,
)

logger = logging.getLogger("carti.ranking")


class RankingService(IRankingService):
    """Candidate Ranking and Explanation service implementing IRankingService."""

    def __init__(
        self,
        config: Optional[RankingConfig] = None,
        comparison_service: Optional[ComparisonService] = None,
    ):
        self.config = config or RankingConfig()
        self.comparison_service = comparison_service or ComparisonService(config=self.config)

    def rank_candidates(
        self,
        candidates: List[Candidate],
        query: str,
        mandate: Mandate,
    ) -> List[Candidate]:
        """Rank candidates deterministically using multi-attribute scoring and update their scores."""
        if not candidates:
            return []

        # Convert mandate model to B7 MandateSnapshot
        mandate_snapshot = MandateSnapshot(
            total_budget=mandate.total_budget,
            currency=mandate.currency,
            per_item_cap=mandate.per_item_cap,
            allowed_categories=mandate.allowed_categories,
            blocked_categories=mandate.blocked_categories,
            allowed_retailers=mandate.allowed_retailers,
            max_quantity=mandate.max_quantity,
            price_tolerance=mandate.price_tolerance,
            status=mandate.status,
            expires_at=mandate.expires_at,
        )

        shopping_request = ShoppingRequest(
            original_text=query,
            currency=mandate.currency,
            max_price=mandate.per_item_cap,
        )

        # Build CandidateOption list
        candidate_options: List[CandidateOption] = []
        cand_map: dict[str, Candidate] = {}

        for cand in candidates:
            cand_id_str = str(cand.id)
            cand_map[cand_id_str] = cand

            # Find active or first offer
            offer_obj = cand.offers[0] if cand.offers else None
            if not offer_obj:
                continue

            b7_prod = CandidateProduct(
                product_id=cand.provider_product_id or cand_id_str,
                title=cand.title,
                brand=cand.brand,
                category=cand.category,
                description=None,
                attributes=cand.attributes or {},
            )
            b7_off = CandidateOffer(
                offer_key=str(offer_obj.id),
                domain=offer_obj.domain,
                buy_url=offer_obj.buy_url,
                price_amount=offer_obj.price_amount,
                currency=offer_obj.currency,
                availability=offer_obj.availability,
                condition=offer_obj.condition or "new",
            )
            option = CandidateOption(
                candidate_id=cand_id_str,
                product=b7_prod,
                offer=b7_off,
            )
            candidate_options.append(option)

        if not candidate_options:
            return candidates

        # Run comparison and ranking
        comparison_result = self.comparison_service.compare_and_rank(
            request=shopping_request,
            candidates=candidate_options,
            mandate=mandate_snapshot,
        )

        # Assign ranking scores and rationale back to candidates
        scored_candidates: List[Candidate] = []
        for ranked in comparison_result.ranked_candidates:
            cand = cand_map.get(ranked.candidate_id)
            if cand:
                cand.rank_score = Decimal(f"{ranked.ranking_score:.4f}")
                cand.rank_reason = f"Ranked #{ranked.ranking_position or 1}: {', '.join(ranked.positive_matching_factors[:2]) or 'Strong match for mandate'}"
                scored_candidates.append(cand)

        # Append any rejected candidates with zero score and rejection reason
        for rej in comparison_result.rejected_candidates:
            cand = cand_map.get(rej.candidate_id)
            if cand and cand not in scored_candidates:
                cand.rank_score = Decimal("0.0000")
                if rej.rejection_reasons:
                    cand.rejected_reason = rej.rejection_reasons[0].reason
                scored_candidates.append(cand)

        return scored_candidates
