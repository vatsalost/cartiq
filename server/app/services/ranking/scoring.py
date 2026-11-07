"""Transparent deterministic scoring engine for eligible candidate options."""

from decimal import Decimal
from typing import Optional
from server.app.services.ranking.config import RankingConfig
from server.app.services.ranking.interfaces import ICandidateScorer
from server.app.services.ranking.models import (
    CandidateOption,
    MandateSnapshot,
    ShoppingRequest,
)


def _clean_str(val: Optional[str]) -> str:
    return (val or "").strip().lower()


class CandidateScorer(ICandidateScorer):
    """Computes weighted, normalized suitability scores with full factor breakdowns."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()

    def score_candidate(
        self,
        candidate: CandidateOption,
        request: ShoppingRequest,
        mandate: Optional[MandateSnapshot] = None,
    ) -> tuple[float, dict[str, float], list[str], list[str]]:
        """Calculate score, granular breakdown, positive matches, and data uncertainties.

        Returns:
            Tuple of:
            - ranking_score: float in [0.0, 1.0]
            - score_breakdown: dict of factor names to normalized float contributions
            - positive_matching_factors: list of fact-based advantages
            - missing_or_uncertain_information: list of unverified data points
        """
        product = candidate.product
        offer = candidate.offer
        weights = self.config.weights

        positive_factors: list[str] = []
        uncertain_info: list[str] = []
        breakdown: dict[str, float] = {}

        # 1. Price Score Factor
        # Determine reference ceiling (request max_price or mandate per_item_cap)
        ref_cap = request.max_price or (mandate.per_item_cap if mandate else None)
        if ref_cap and ref_cap > Decimal("0.00"):
            # Normalize price relative to ceiling: lower price yields higher savings efficiency
            ratio = float(offer.price_amount / ref_cap)
            # Cap ratio at 1.0 (since candidate is eligible)
            price_score = max(0.0, min(1.0, 1.0 - (0.5 * ratio)))
            savings = ref_cap - offer.price_amount
            if savings >= Decimal("0.00"):
                positive_factors.append(
                    f"Listed at {offer.price_amount} {offer.currency}, staying under the {ref_cap} {offer.currency} limit "
                    f"with {savings} {offer.currency} in headroom."
                )
        else:
            # Neutral baseline score when no ceiling is defined
            price_score = 0.80

        breakdown["price_factor"] = round(price_score, 4)

        # 2. Preferred Attributes Match Factor
        if request.preferred_attributes:
            prod_attrs = {_clean_str(k): _clean_str(v) for k, v in product.attributes.items()}
            searchable_text = f"{_clean_str(product.title)} {_clean_str(product.description)}"

            matched_count = 0
            for pref_k, pref_v in request.preferred_attributes.items():
                k_clean = _clean_str(pref_k)
                v_clean = _clean_str(pref_v)

                if (k_clean in prod_attrs and v_clean in prod_attrs[k_clean]) or v_clean in searchable_text:
                    matched_count += 1
                    positive_factors.append(f"Satisfies preferred attribute '{pref_k}': '{pref_v}'.")
                else:
                    uncertain_info.append(f"Preferred attribute '{pref_k}': '{pref_v}' not verified in catalog.")

            pref_attr_score = matched_count / len(request.preferred_attributes)
        else:
            pref_attr_score = 1.0  # Neutral if user has no preferred attributes

        breakdown["preferred_attributes_factor"] = round(pref_attr_score, 4)

        # 3. Brand Preference Factor
        if request.preferred_brands:
            prod_brand = _clean_str(product.brand)
            preferred_brands_norm = {_clean_str(b) for b in request.preferred_brands}

            if prod_brand and prod_brand in preferred_brands_norm:
                brand_score = 1.0
                positive_factors.append(f"Matches preferred brand: '{product.brand}'.")
            else:
                brand_score = 0.20
                if not prod_brand:
                    uncertain_info.append("Brand name is missing from catalog data.")
        else:
            brand_score = 0.80  # Neutral

        breakdown["brand_preference_factor"] = round(brand_score, 4)

        # 4. Retailer Preference Factor
        offer_domain_clean = _clean_str(offer.domain).removeprefix("www.")
        if request.preferred_retailers:
            preferred_retailers_norm = {_clean_str(r).removeprefix("www.") for r in request.preferred_retailers}

            if offer_domain_clean in preferred_retailers_norm:
                retailer_score = 1.0
                positive_factors.append(f"Offered by preferred merchant: '{offer.domain}'.")
            else:
                retailer_score = 0.30
        else:
            retailer_score = 0.85  # Neutral

        breakdown["retailer_preference_factor"] = round(retailer_score, 4)

        # 5. Condition Factor
        cond_clean = _clean_str(offer.condition)
        if cond_clean == "new":
            cond_score = 1.0
            positive_factors.append("Condition confirmed as brand new.")
        elif cond_clean in ("refurbished", "used"):
            cond_score = 0.60
            uncertain_info.append(f"Item condition is listed as '{offer.condition}'.")
        else:
            cond_score = 0.40
            uncertain_info.append("Item condition is unspecified or unknown.")

        breakdown["condition_factor"] = round(cond_score, 4)

        # 6. Data Quality & Completeness Factor
        completeness_pts = 0.0
        if product.image_url:
            completeness_pts += 0.5
        else:
            uncertain_info.append("Primary product image is missing.")

        if product.description and len(product.description.strip()) > 20:
            completeness_pts += 0.5
        else:
            uncertain_info.append("Detailed product description is missing.")

        breakdown["data_quality_factor"] = round(completeness_pts, 4)

        # Weighted Aggregate Score Calculation
        total_weight = (
            weights.price_weight
            + weights.preferred_attributes_weight
            + weights.preferred_brands_weight
            + weights.preferred_retailers_weight
            + weights.condition_weight
            + weights.data_quality_weight
        )

        raw_score = (
            (price_score * weights.price_weight)
            + (pref_attr_score * weights.preferred_attributes_weight)
            + (brand_score * weights.preferred_brands_weight)
            + (retailer_score * weights.preferred_retailers_weight)
            + (cond_score * weights.condition_weight)
            + (completeness_pts * weights.data_quality_weight)
        ) / total_weight

        # Strictly clamp ranking score between 0.0 and 1.0
        final_score = round(max(0.0, min(1.0, raw_score)), 4)

        return final_score, breakdown, positive_factors, uncertain_info
