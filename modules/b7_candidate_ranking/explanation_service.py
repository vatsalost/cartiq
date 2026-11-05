"""Fact-grounded explanation service for recommendations and alternative exclusions."""

import logging
from typing import Optional
from modules.b7_candidate_ranking.config import RankingConfig
from modules.b7_candidate_ranking.interfaces import (
    IExplanationGenerator,
    ILLMExplanationAdapter,
)
from modules.b7_candidate_ranking.models import (
    RankedCandidate,
    ShoppingRequest,
)

logger = logging.getLogger("cartiq.ranking.explanation")


class ExplanationService(IExplanationGenerator):
    """Generates concise, factual rationales for the selected candidate and excluded alternatives.

    Explanations strictly adhere to verified product attributes, pricing, and availability.
    """

    def __init__(
        self,
        config: Optional[RankingConfig] = None,
        llm_adapter: Optional[ILLMExplanationAdapter] = None,
    ):
        self.config = config or RankingConfig()
        self.llm_adapter = llm_adapter

    def generate_explanation(
        self,
        request: ShoppingRequest,
        ranked_candidates: list[RankedCandidate],
        rejected_candidates: list[RankedCandidate],
    ) -> str:
        """Construct a deterministic, evidence-based explanation.

        Falls back safely to deterministic templates if no LLM adapter is configured or if
        the adapter fails.
        """
        if not ranked_candidates:
            if rejected_candidates:
                first_rejected = rejected_candidates[0]
                reasons = "; ".join(r.reason for r in first_rejected.rejection_reasons)
                return (
                    f"No eligible candidates found. All options were excluded based on constraints. "
                    f"For example, '{first_rejected.product_title}' from {first_rejected.domain} "
                    f"was excluded because: {reasons}."
                )
            return "No matching products or offers were found for your request."

        selected = ranked_candidates[0]

        # 1. Assemble verified facts about the selected choice
        fact_clauses: list[str] = []

        # Positive matching attributes
        if selected.positive_matching_factors:
            # Use top positive factors
            top_factors = selected.positive_matching_factors[:2]
            fact_clauses.append(", ".join(top_factors).lower())

        # Price grounding
        price_clause = f"priced at {selected.price_amount} {selected.currency} from {selected.domain}"
        if request.max_price:
            price_clause += f" (under your {request.max_price} {request.currency} limit)"
        fact_clauses.append(price_clause)

        # Availability grounding
        if selected.availability.lower() in ("instock", "in_stock", "available"):
            fact_clauses.append("confirmed in stock")

        explanation_parts: list[str] = []
        explanation_parts.append(
            f"Selected '{selected.product_title}' because it is " + ", and ".join(fact_clauses) + "."
        )

        # 2. Alternative Comparison (runner-up or excluded alternative)
        if len(ranked_candidates) > 1:
            runner_up = ranked_candidates[1]
            diff = runner_up.price_amount - selected.price_amount
            if diff > 0:
                explanation_parts.append(
                    f"It ranked higher than '{runner_up.product_title}' from {runner_up.domain} "
                    f"({runner_up.price_amount} {runner_up.currency}), offering a {diff} {selected.currency} savings."
                )
            else:
                explanation_parts.append(
                    f"It was selected over '{runner_up.product_title}' from {runner_up.domain} "
                    f"due to closer alignment with your specified preferences."
                )
        elif rejected_candidates:
            # Explain why the most prominent alternative was rejected
            rejected_alt = rejected_candidates[0]
            if rejected_alt.rejection_reasons:
                primary_reason = rejected_alt.rejection_reasons[0].reason
                explanation_parts.append(
                    f"An alternative '{rejected_alt.product_title}' from {rejected_alt.domain} "
                    f"was excluded because {primary_reason.lower()}."
                )

        # 3. Transparent note regarding data uncertainty if any
        if selected.missing_or_uncertain_information:
            note = selected.missing_or_uncertain_information[0]
            explanation_parts.append(f"Note: {note}")

        full_explanation = " ".join(explanation_parts)

        # Enforce length limit safely
        if len(full_explanation) > self.config.max_explanation_length:
            full_explanation = full_explanation[: self.config.max_explanation_length - 3] + "..."

        return full_explanation
