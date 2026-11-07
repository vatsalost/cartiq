"""Deterministic pre-filtering engine for candidate options."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from server.app.services.ranking.config import RankingConfig
from server.app.services.ranking.interfaces import IEligibilityFilter
from server.app.services.ranking.models import (
    CandidateOption,
    MandateSnapshot,
    RejectionCode,
    RejectionDetail,
    ShoppingRequest,
)

VALID_IN_STOCK_STRINGS = {"instock", "in_stock", "available", "true"}


def _normalize_string(val: Optional[str]) -> str:
    return (val or "").strip().lower().replace("_", "").replace("-", "").replace(" ", "")


def _normalize_domain(domain: Optional[str]) -> str:
    clean = (domain or "").strip().lower()
    if clean.startswith("http://"):
        clean = clean[7:]
    elif clean.startswith("https://"):
        clean = clean[8:]
    return clean.removeprefix("www.").split("/")[0].split(":")[0]


class EligibilityFilter(IEligibilityFilter):
    """Evaluates candidate options against hard constraints and preserves all failure reasons."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()

    def evaluate(
        self,
        candidate: CandidateOption,
        request: ShoppingRequest,
        mandate: Optional[MandateSnapshot] = None,
        now: Optional[datetime] = None,
    ) -> list[RejectionDetail]:
        """Perform comprehensive deterministic checks against a candidate option.

        Preserves all applicable rejection reasons rather than aborting early.
        """
        rejections: list[RejectionDetail] = []
        product = candidate.product
        offer = candidate.offer
        current_time = now or datetime.now(timezone.utc)

        # 1. Insufficient product metadata
        if not product.product_id or not product.product_id.strip() or not product.title or not product.title.strip():
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.INSUFFICIENT_PRODUCT_DATA,
                    reason="Product is missing a valid canonical ID or display title.",
                )
            )

        # 2. Invalid or incomplete offer data
        if not offer.offer_key or not offer.offer_key.strip() or not offer.domain or not offer.buy_url:
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.INVALID_OFFER_DATA,
                    reason="Offer lacks critical identifiers, merchant domain, or buy link.",
                )
            )
        elif offer.price_amount is None or offer.price_amount <= Decimal("0.00"):
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.INVALID_OFFER_DATA,
                    reason=f"Offer has an invalid or non-positive price: {offer.price_amount}.",
                )
            )

        # 3. Availability Check (Do not assume unknown availability is in stock)
        norm_avail = _normalize_string(offer.availability)
        if norm_avail not in VALID_IN_STOCK_STRINGS:
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.OUT_OF_STOCK,
                    reason=f"Offer is not confirmed in-stock (status: '{offer.availability}').",
                )
            )

        # 4. Currency Check (Do not silently convert currencies)
        if request.currency and offer.currency.upper() != request.currency.upper():
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.WRONG_CURRENCY,
                    reason=(
                        f"Offer currency '{offer.currency}' does not match requested currency "
                        f"'{request.currency}'."
                    ),
                )
            )
        elif mandate and mandate.currency and offer.currency.upper() != mandate.currency.upper():
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.WRONG_CURRENCY,
                    reason=(
                        f"Offer currency '{offer.currency}' does not match mandate currency "
                        f"'{mandate.currency}'."
                    ),
                )
            )

        # 5. User Maximum Price Limit
        if request.max_price is not None and offer.price_amount > request.max_price:
            rejections.append(
                RejectionDetail(
                    code=RejectionCode.ABOVE_REQUEST_PRICE_LIMIT,
                    reason=(
                        f"Offer price {offer.price_amount} {offer.currency} exceeds "
                        f"requested maximum of {request.max_price} {request.currency}."
                    ),
                )
            )

        # 6. Mandate Per-Item Cap and Total Budget
        if mandate:
            if mandate.per_item_cap is not None and offer.price_amount > mandate.per_item_cap:
                rejections.append(
                    RejectionDetail(
                        code=RejectionCode.ABOVE_PER_ITEM_CAP,
                        reason=(
                            f"Offer price {offer.price_amount} {offer.currency} exceeds "
                            f"mandate per-item cap of {mandate.per_item_cap} {mandate.currency}."
                        ),
                    )
                )
            if mandate.total_budget is not None and offer.price_amount > mandate.total_budget:
                rejections.append(
                    RejectionDetail(
                        code=RejectionCode.ABOVE_PER_ITEM_CAP,
                        reason=(
                            f"Offer price {offer.price_amount} {offer.currency} exceeds "
                            f"total mandate budget of {mandate.total_budget} {mandate.currency}."
                        ),
                    )
                )

        # 7. Category Restrictions
        prod_cat_norm = (product.category or "").strip().lower()
        if mandate and mandate.blocked_categories:
            for blocked in mandate.blocked_categories:
                blocked_norm = blocked.strip().lower()
                if blocked_norm and (blocked_norm == prod_cat_norm or blocked_norm in prod_cat_norm):
                    rejections.append(
                        RejectionDetail(
                            code=RejectionCode.BLOCKED_CATEGORY,
                            reason=f"Product category '{product.category}' matches prohibited category '{blocked}'.",
                        )
                    )
                    break

        if mandate and mandate.allowed_categories is not None:
            allowed_normalized = {c.strip().lower() for c in mandate.allowed_categories if c.strip()}
            if prod_cat_norm not in allowed_normalized and not any(a in prod_cat_norm for a in allowed_normalized):
                rejections.append(
                    RejectionDetail(
                        code=RejectionCode.CATEGORY_NOT_ALLOWED,
                        reason=f"Product category '{product.category}' is not in allowed categories.",
                    )
                )

        # 8. Retailer Allowlist
        if mandate and mandate.allowed_retailers is not None:
            clean_offer_domain = _normalize_domain(offer.domain)
            allowed_domains = {_normalize_domain(r) for r in mandate.allowed_retailers}
            if clean_offer_domain not in allowed_domains:
                rejections.append(
                    RejectionDetail(
                        code=RejectionCode.RETAILER_NOT_ALLOWED,
                        reason=f"Retailer domain '{offer.domain}' is not in the approved retailer allowlist.",
                    )
                )

        # 9. Condition Check (Do not assume unknown condition means new)
        if request.required_condition:
            req_cond = request.required_condition.strip().lower()
            offer_cond = (offer.condition or "unknown").strip().lower()
            if req_cond != offer_cond:
                rejections.append(
                    RejectionDetail(
                        code=RejectionCode.WRONG_CONDITION,
                        reason=(
                            f"Offer condition '{offer.condition}' does not match required "
                            f"condition '{request.required_condition}'."
                        ),
                    )
                )

        # 10. Missing Required Attributes
        if request.required_attributes:
            prod_attrs = {str(k).strip().lower(): str(v).strip().lower() for k, v in product.attributes.items()}
            # Also search description or title for text-based attributes if appropriate
            searchable_text = f"{product.title} {product.description or ''}".lower()

            for req_key, req_val in request.required_attributes.items():
                k_clean = str(req_key).strip().lower()
                v_clean = str(req_val).strip().lower()

                matched = False
                if k_clean in prod_attrs:
                    actual_val = prod_attrs[k_clean]
                    if v_clean in actual_val or actual_val in v_clean:
                        matched = True
                elif v_clean in searchable_text:
                    matched = True

                if not matched:
                    rejections.append(
                        RejectionDetail(
                            code=RejectionCode.MISSING_REQUIRED_ATTRIBUTE,
                            reason=f"Product lacks required attribute '{req_key}' with value '{req_val}'.",
                        )
                    )

        # 11. Stale Product / Offer Data
        if offer.observed_at:
            # Normalize timestamps to UTC
            obs_utc = offer.observed_at.astimezone(timezone.utc) if offer.observed_at.tzinfo else offer.observed_at.replace(tzinfo=timezone.utc)
            now_utc = current_time.astimezone(timezone.utc) if current_time.tzinfo else current_time.replace(tzinfo=timezone.utc)
            age_seconds = (now_utc - obs_utc).total_seconds()
            if age_seconds > self.config.max_data_age_seconds:
                rejections.append(
                    RejectionDetail(
                        code=RejectionCode.STALE_PRODUCT_DATA,
                        reason=(
                            f"Offer data is stale (observed {int(age_seconds)}s ago, "
                            f"maximum allowed is {self.config.max_data_age_seconds}s)."
                        ),
                    )
                )

        return rejections
