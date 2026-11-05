"""
Deterministic policy rules for Module B8 — Guardrail & Policy Engine.

Each function evaluates one specific, named policy rule and returns a
PolicyRuleResult. Rules are independent and stateless; they receive only
the data they need as typed arguments.

Design guarantees:
- Every rule is a pure function: same inputs always produce same output.
- No LLM is called; no external state is accessed.
- Currency conversion is NEVER performed silently.
- Budget checks use Decimal arithmetic to prevent floating-point drift.
- Unknown or missing data fails safe (not silently approved).
"""

import logging
from decimal import Decimal
from typing import Optional

from server.app.services.guardrails.models import PolicyRuleResult, PolicyViolationCode

logger = logging.getLogger("cartiq.b8.policy_rules")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_VALID_IN_STOCK_STRINGS: frozenset[str] = frozenset(
    {"instock", "in_stock", "available", "true"}
)


def _norm(val: Optional[str]) -> str:
    """Normalize a string for case-insensitive, whitespace-insensitive comparison."""
    return (val or "").strip().lower().replace("_", "").replace("-", "").replace(" ", "")


def _norm_domain(domain: Optional[str]) -> str:
    """Strip protocol, www prefix, and path from a domain string."""
    clean = (domain or "").strip().lower()
    for prefix in ("https://", "http://"):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean.removeprefix("www.").split("/")[0].split(":")[0]


# ---------------------------------------------------------------------------
# Budget & spending limit rules
# ---------------------------------------------------------------------------

def rule_budget_not_exceeded(
    price_amount: Decimal,
    offer_currency: str,
    total_budget: Optional[Decimal],
    mandate_currency: str,
) -> PolicyRuleResult:
    """Verify that the offer price does not exceed the mandate's total budget ceiling.

    Note: This checks the offer price against the declared total_budget ceiling.
    Available-budget (accounting for reservations/spend) is a runtime DB concern
    handled at the proposal/checkout layer, not inside the stateless policy engine.
    """
    if total_budget is None:
        return PolicyRuleResult(
            rule_name="budget_ceiling_check",
            passed=True,
            violation_code=None,
            detail="No total_budget ceiling defined in mandate; budget ceiling rule skipped.",
        )

    if offer_currency.upper() != mandate_currency.upper():
        # Currency mismatch prevents meaningful comparison — handled by currency rule.
        return PolicyRuleResult(
            rule_name="budget_ceiling_check",
            passed=True,
            violation_code=None,
            detail=(
                f"Currency mismatch ({offer_currency} vs {mandate_currency}) detected; "
                "budget ceiling check deferred to currency rule."
            ),
        )

    if price_amount > total_budget:
        return PolicyRuleResult(
            rule_name="budget_ceiling_check",
            passed=False,
            violation_code=PolicyViolationCode.BUDGET_EXCEEDED,
            detail=(
                f"Offer price {price_amount} {offer_currency} exceeds the mandate total budget "
                f"ceiling of {total_budget} {mandate_currency}."
            ),
        )

    return PolicyRuleResult(
        rule_name="budget_ceiling_check",
        passed=True,
        violation_code=None,
        detail=(
            f"Offer price {price_amount} {offer_currency} is within mandate total budget "
            f"ceiling of {total_budget} {mandate_currency}."
        ),
    )


def rule_per_item_cap(
    price_amount: Decimal,
    offer_currency: str,
    per_item_cap: Optional[Decimal],
    mandate_currency: str,
) -> PolicyRuleResult:
    """Verify that the offer price does not exceed the mandate's per-item spending cap."""
    if per_item_cap is None:
        return PolicyRuleResult(
            rule_name="per_item_cap_check",
            passed=True,
            violation_code=None,
            detail="No per_item_cap defined in mandate; per-item cap check skipped.",
        )

    if offer_currency.upper() != mandate_currency.upper():
        return PolicyRuleResult(
            rule_name="per_item_cap_check",
            passed=True,
            violation_code=None,
            detail=(
                f"Currency mismatch ({offer_currency} vs {mandate_currency}); "
                "per-item cap check deferred to currency rule."
            ),
        )

    if price_amount > per_item_cap:
        return PolicyRuleResult(
            rule_name="per_item_cap_check",
            passed=False,
            violation_code=PolicyViolationCode.PER_ITEM_CAP_EXCEEDED,
            detail=(
                f"Offer price {price_amount} {offer_currency} exceeds the mandate per-item cap "
                f"of {per_item_cap} {mandate_currency}."
            ),
        )

    return PolicyRuleResult(
        rule_name="per_item_cap_check",
        passed=True,
        violation_code=None,
        detail=(
            f"Offer price {price_amount} {offer_currency} is within mandate per-item cap "
            f"of {per_item_cap} {mandate_currency}."
        ),
    )


# ---------------------------------------------------------------------------
# Category rules
# ---------------------------------------------------------------------------

def rule_category_not_blocked(
    product_category: Optional[str],
    blocked_categories: Optional[list[str]],
) -> PolicyRuleResult:
    """Verify that the product category is not in the mandate's blocked category list."""
    if not blocked_categories:
        return PolicyRuleResult(
            rule_name="blocked_category_check",
            passed=True,
            violation_code=None,
            detail="No blocked_categories defined in mandate; blocked category check skipped.",
        )

    prod_cat_norm = _norm(product_category)

    for blocked in blocked_categories:
        blocked_norm = _norm(blocked)
        if blocked_norm and (blocked_norm == prod_cat_norm or blocked_norm in prod_cat_norm):
            return PolicyRuleResult(
                rule_name="blocked_category_check",
                passed=False,
                violation_code=PolicyViolationCode.BLOCKED_CATEGORY,
                detail=(
                    f"Product category '{product_category}' matches mandate-prohibited "
                    f"category '{blocked}'."
                ),
            )

    return PolicyRuleResult(
        rule_name="blocked_category_check",
        passed=True,
        violation_code=None,
        detail=f"Product category '{product_category}' is not in the mandate's blocked category list.",
    )


def rule_category_allowed(
    product_category: Optional[str],
    allowed_categories: Optional[list[str]],
) -> PolicyRuleResult:
    """Verify that the product category appears in the mandate's allowed category list.

    When allowed_categories is None (not set), all categories are permitted.
    When allowed_categories is an empty list, NO category is permitted.
    """
    if allowed_categories is None:
        return PolicyRuleResult(
            rule_name="allowed_category_check",
            passed=True,
            violation_code=None,
            detail="No allowed_categories allowlist defined in mandate; all categories permitted.",
        )

    prod_cat_norm = _norm(product_category)
    allowed_normalized = {_norm(c) for c in allowed_categories if c and c.strip()}

    if not allowed_normalized:
        # Allowlist is defined but empty — no category is permitted.
        return PolicyRuleResult(
            rule_name="allowed_category_check",
            passed=False,
            violation_code=PolicyViolationCode.CATEGORY_NOT_ALLOWED,
            detail=(
                f"Product category '{product_category}' is not permitted. "
                "The mandate allowed_categories list is defined but contains no entries."
            ),
        )

    if prod_cat_norm in allowed_normalized or any(a in prod_cat_norm for a in allowed_normalized):
        return PolicyRuleResult(
            rule_name="allowed_category_check",
            passed=True,
            violation_code=None,
            detail=f"Product category '{product_category}' is in the mandate's allowed category list.",
        )

    return PolicyRuleResult(
        rule_name="allowed_category_check",
        passed=False,
        violation_code=PolicyViolationCode.CATEGORY_NOT_ALLOWED,
        detail=(
            f"Product category '{product_category}' is not in the mandate's allowed categories. "
            f"Permitted: {sorted(allowed_categories)}."
        ),
    )


# ---------------------------------------------------------------------------
# Retailer rule
# ---------------------------------------------------------------------------

def rule_retailer_allowed(
    offer_domain: str,
    allowed_retailers: Optional[list[str]],
) -> PolicyRuleResult:
    """Verify that the offer's retailer domain is in the mandate's approved retailer allowlist."""
    if allowed_retailers is None:
        return PolicyRuleResult(
            rule_name="allowed_retailer_check",
            passed=True,
            violation_code=None,
            detail="No allowed_retailers allowlist defined in mandate; all retailers permitted.",
        )

    clean_offer_domain = _norm_domain(offer_domain)
    allowed_domains = {_norm_domain(r) for r in allowed_retailers}

    if clean_offer_domain in allowed_domains:
        return PolicyRuleResult(
            rule_name="allowed_retailer_check",
            passed=True,
            violation_code=None,
            detail=f"Retailer domain '{offer_domain}' is in the mandate's approved retailer allowlist.",
        )

    return PolicyRuleResult(
        rule_name="allowed_retailer_check",
        passed=False,
        violation_code=PolicyViolationCode.RETAILER_NOT_ALLOWED,
        detail=(
            f"Retailer domain '{offer_domain}' is not in the mandate's approved allowlist. "
            f"Approved retailers: {sorted(allowed_retailers)}."
        ),
    )


# ---------------------------------------------------------------------------
# Quantity rule
# ---------------------------------------------------------------------------

def rule_quantity_within_limit(
    quantity: int,
    max_quantity: Optional[int],
) -> PolicyRuleResult:
    """Verify that the requested quantity does not exceed the mandate's maximum."""
    if max_quantity is None:
        return PolicyRuleResult(
            rule_name="quantity_limit_check",
            passed=True,
            violation_code=None,
            detail="No max_quantity defined in mandate; quantity check skipped.",
        )

    if quantity > max_quantity:
        return PolicyRuleResult(
            rule_name="quantity_limit_check",
            passed=False,
            violation_code=PolicyViolationCode.QUANTITY_EXCEEDED,
            detail=(
                f"Requested quantity {quantity} exceeds the mandate maximum of {max_quantity}."
            ),
        )

    return PolicyRuleResult(
        rule_name="quantity_limit_check",
        passed=True,
        violation_code=None,
        detail=f"Requested quantity {quantity} is within mandate maximum of {max_quantity}.",
    )


# ---------------------------------------------------------------------------
# Currency rule
# ---------------------------------------------------------------------------

def rule_currency_consistent(
    offer_currency: str,
    mandate_currency: str,
) -> PolicyRuleResult:
    """Verify that the offer's currency matches the mandate currency exactly.

    Silent currency conversion is NEVER performed by B8.
    """
    if offer_currency.strip().upper() == mandate_currency.strip().upper():
        return PolicyRuleResult(
            rule_name="currency_consistency_check",
            passed=True,
            violation_code=None,
            detail=(
                f"Offer currency '{offer_currency}' matches mandate currency '{mandate_currency}'."
            ),
        )

    return PolicyRuleResult(
        rule_name="currency_consistency_check",
        passed=False,
        violation_code=PolicyViolationCode.CURRENCY_MISMATCH,
        detail=(
            f"Offer currency '{offer_currency}' does not match mandate currency '{mandate_currency}'. "
            "B8 never performs silent currency conversion."
        ),
    )


# ---------------------------------------------------------------------------
# Offer data validity rules
# ---------------------------------------------------------------------------

def rule_offer_price_valid(
    price_amount: Optional[Decimal],
    offer_key: Optional[str],
    buy_url: Optional[str],
    domain: Optional[str],
) -> PolicyRuleResult:
    """Verify that the offer has a valid, positive price and essential identifiers."""
    if not offer_key or not offer_key.strip():
        return PolicyRuleResult(
            rule_name="offer_data_validity_check",
            passed=False,
            violation_code=PolicyViolationCode.INVALID_OFFER_DATA,
            detail="Offer is missing a valid offer_key identifier.",
        )

    if not domain or not domain.strip():
        return PolicyRuleResult(
            rule_name="offer_data_validity_check",
            passed=False,
            violation_code=PolicyViolationCode.INVALID_OFFER_DATA,
            detail="Offer is missing a valid retailer domain.",
        )

    if not buy_url or not buy_url.strip():
        return PolicyRuleResult(
            rule_name="offer_data_validity_check",
            passed=False,
            violation_code=PolicyViolationCode.INVALID_OFFER_DATA,
            detail="Offer is missing a valid buy_url (purchase link).",
        )

    if price_amount is None or price_amount <= Decimal("0.00"):
        return PolicyRuleResult(
            rule_name="offer_data_validity_check",
            passed=False,
            violation_code=PolicyViolationCode.INVALID_PRICE,
            detail=f"Offer has an invalid or non-positive price: {price_amount!r}.",
        )

    return PolicyRuleResult(
        rule_name="offer_data_validity_check",
        passed=True,
        violation_code=None,
        detail=f"Offer data is structurally valid (price={price_amount}, domain='{domain}').",
    )


def rule_offer_in_stock(availability: str) -> PolicyRuleResult:
    """Verify that the offer is confirmed in-stock.

    Unknown availability is NOT assumed in-stock and will fail this rule.
    """
    norm_avail = _norm(availability)
    if norm_avail in _VALID_IN_STOCK_STRINGS:
        return PolicyRuleResult(
            rule_name="offer_stock_check",
            passed=True,
            violation_code=None,
            detail=f"Offer availability '{availability}' is confirmed in-stock.",
        )

    return PolicyRuleResult(
        rule_name="offer_stock_check",
        passed=False,
        violation_code=PolicyViolationCode.OUT_OF_STOCK,
        detail=(
            f"Offer availability '{availability}' is not confirmed in-stock. "
            "Unknown or out-of-stock availability cannot be authorized."
        ),
    )


def rule_product_data_valid(
    product_id: Optional[str],
    product_title: Optional[str],
) -> PolicyRuleResult:
    """Verify that the product has the minimum required identity fields."""
    if not product_id or not product_id.strip():
        return PolicyRuleResult(
            rule_name="product_data_validity_check",
            passed=False,
            violation_code=PolicyViolationCode.INVALID_PRODUCT_DATA,
            detail="Product is missing a valid canonical product_id.",
        )

    if not product_title or not product_title.strip():
        return PolicyRuleResult(
            rule_name="product_data_validity_check",
            passed=False,
            violation_code=PolicyViolationCode.INVALID_PRODUCT_DATA,
            detail="Product is missing a valid display title.",
        )

    return PolicyRuleResult(
        rule_name="product_data_validity_check",
        passed=True,
        violation_code=None,
        detail=f"Product data is valid (id='{product_id}', title='{product_title}').",
    )


# ---------------------------------------------------------------------------
# Price tolerance rule
# ---------------------------------------------------------------------------

def rule_price_within_tolerance(
    price_amount: Decimal,
    reference_price: Decimal,
    price_tolerance: Optional[Decimal],
    currency: str,
) -> PolicyRuleResult:
    """Verify that the offer price has not drifted beyond the mandate's price tolerance.

    Used when a proposal was approved at a reference price and the actual offer
    price must be re-verified before checkout.
    """
    if price_tolerance is None:
        return PolicyRuleResult(
            rule_name="price_tolerance_check",
            passed=True,
            violation_code=None,
            detail="No price_tolerance defined in mandate; price tolerance check skipped.",
        )

    drift = abs(price_amount - reference_price)
    if drift > price_tolerance:
        return PolicyRuleResult(
            rule_name="price_tolerance_check",
            passed=False,
            violation_code=PolicyViolationCode.PRICE_TOLERANCE_EXCEEDED,
            detail=(
                f"Offer price {price_amount} {currency} has drifted {drift} {currency} from "
                f"reference price {reference_price} {currency}, exceeding the mandate tolerance "
                f"of {price_tolerance} {currency}."
            ),
        )

    return PolicyRuleResult(
        rule_name="price_tolerance_check",
        passed=True,
        violation_code=None,
        detail=(
            f"Offer price {price_amount} {currency} is within {price_tolerance} {currency} "
            f"tolerance of reference price {reference_price} {currency}."
        ),
    )


# ---------------------------------------------------------------------------
# Condition and attribute rules
# ---------------------------------------------------------------------------

def rule_condition_allowed(
    offer_condition: str,
    required_condition: Optional[str],
) -> PolicyRuleResult:
    """Verify that the offer condition satisfies the requested condition."""
    if not required_condition:
        return PolicyRuleResult(
            rule_name="condition_check",
            passed=True,
            violation_code=None,
            detail="No required_condition specified; condition check passed.",
        )

    norm_req = _norm(required_condition)
    norm_offer = _norm(offer_condition)
    if norm_req == norm_offer:
        return PolicyRuleResult(
            rule_name="condition_check",
            passed=True,
            violation_code=None,
            detail=f"Offer condition '{offer_condition}' matches required condition '{required_condition}'.",
        )

    return PolicyRuleResult(
        rule_name="condition_check",
        passed=False,
        violation_code=PolicyViolationCode.WRONG_CONDITION,
        detail=(
            f"Offer condition '{offer_condition}' does not match required condition '{required_condition}'."
        ),
    )


def rule_required_attributes_satisfied(
    attributes: dict,
    required_attributes: Optional[dict],
    product_title: Optional[str] = None,
) -> PolicyRuleResult:
    """Verify that all required attributes are satisfied."""
    if not required_attributes:
        return PolicyRuleResult(
            rule_name="required_attributes_check",
            passed=True,
            violation_code=None,
            detail="No required_attributes specified; attribute check passed.",
        )

    clean_attrs = {_norm(str(k)): _norm(str(v)) for k, v in (attributes or {}).items()}
    title_norm = _norm(product_title)

    for req_k, req_v in required_attributes.items():
        k_norm = _norm(str(req_k))
        v_norm = _norm(str(req_v))

        matched = False
        if k_norm in clean_attrs and (v_norm in clean_attrs[k_norm] or clean_attrs[k_norm] in v_norm):
            matched = True
        elif v_norm in title_norm:
            matched = True

        if not matched:
            return PolicyRuleResult(
                rule_name="required_attributes_check",
                passed=False,
                violation_code=PolicyViolationCode.MISSING_REQUIRED_ATTRIBUTE,
                detail=f"Product lacks required attribute '{req_k}' with value '{req_v}'.",
            )

    return PolicyRuleResult(
        rule_name="required_attributes_check",
        passed=True,
        violation_code=None,
        detail="All required attributes are verified and satisfied.",
    )
