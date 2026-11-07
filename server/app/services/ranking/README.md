# 🏆 Module B7: Candidate Ranking & Explanation Service

Part of the **CartiQ Agentic Shopping Concierge**.

---

## 📖 1. Module Overview

Module B7 transforms raw candidate options (products and retailer offers from Channel3 via Module B6) into a structured, transparently ranked comparison list. It evaluates candidate suitability against buyer shopping requests and financial spending mandates, deterministically excludes ineligible options with specific rejection codes, applies a configurable multi-factor scoring algorithm with deterministic tie-breaking, and generates fact-grounded explanations.

### Core Architecture & Boundaries

```
[B6: Channel3 Normalizer]
           │
           ▼ (Candidate Products & Offers)
┌─────────────────────────────────────────────────────────┐
│ MODULE B7: CANDIDATE RANKING & EXPLANATION              │
│                                                         │
│  1. Deterministic Pre-Filtering (12 Rejection Checks)   │
│  2. Configurable Multi-Factor Scoring (0.0 to 1.0)      │
│  3. Deterministic Tie-Breaking & Position Assignment     │
│  4. Fact-Grounded Explanation Engine                    │
│  5. Structured Rejection Audit Trail                    │
└─────────────────────────────────────────────────────────┘
           │
           ▼ (Ranked & Explained Candidate)
[B8: Authoritative Financial Guardrail Engine] (Final Purchase Authorization)
```

> [!IMPORTANT]
> **Separation of Responsibilities**: B7 filters, ranks, and explains candidate recommendations for the AI concierge. Passing B7 eligibility does **NOT** grant purchase authorization. Final purchase approval and payment execution are strictly reserved for **Module B8** and server-side PayPal checkout.

---

## 🛡️ 2. Non-Responsibilities & Guardrails

- **Zero Payment Primitives**: B7 contains **no payment credentials, capture calls, order creation, or refund endpoints**.
- **No LLM Authority**: Scoring and eligibility are 100% deterministic Python code. LLM decisions are never authoritative.
- **No Silent Substitutions**: B7 will never automatically swap out an offer for another merchant or alter prices.
- **Exact Decimal Arithmetic**: All monetary comparisons use Python's `Decimal` to avoid floating-point drift.
- **Untrusted External Data**: Product descriptions and merchant text are treated strictly as untrusted string data; no code or prompt injections are executed.

---

## 📋 3. Rejection Codes & Pre-Filtering Checks

Candidates failing any of the following 12 hard checks are classified as `INELIGIBLE` and preserved with specific `RejectionDetail` records:

| Code | Evaluation Rule |
| :--- | :--- |
| `OUT_OF_STOCK` | Offer status is not verified in-stock (e.g. `OutOfStock`, `Unknown`). |
| `WRONG_CURRENCY` | Offer currency does not match requested currency or mandate currency. |
| `ABOVE_REQUEST_PRICE_LIMIT` | Offer price exceeds buyer's requested `max_price`. |
| `ABOVE_PER_ITEM_CAP` | Offer price exceeds mandate `per_item_cap` or `total_budget`. |
| `BLOCKED_CATEGORY` | Product category matches prohibited category in mandate. |
| `CATEGORY_NOT_ALLOWED` | Product category is not present in mandate's allowed category list. |
| `RETAILER_NOT_ALLOWED` | Merchant domain is outside mandate's approved retailer allowlist. |
| `WRONG_CONDITION` | Offer condition does not match required condition (e.g. refurbished vs new). |
| `MISSING_REQUIRED_ATTRIBUTE` | Mandatory attribute specified in request is missing or mismatched. |
| `INSUFFICIENT_PRODUCT_DATA` | Canonical product ID or display title is missing or blank. |
| `STALE_PRODUCT_DATA` | Offer observation timestamp exceeds `max_data_age_seconds` (default: 24h). |
| `INVALID_OFFER_DATA` | Missing offer key, non-positive price, or missing merchant buy URL. |

---

## ⚖️ 4. Configurable Scoring Algorithm

Eligible candidates are scored on a normalized scale from `0.0` to `1.0`:

$$\text{Final Score} = \frac{\sum (w_i \cdot s_i)}{\sum w_i}$$

### Default Factor Weights:
- **`price_weight` (0.35)**: Relative price compared to ceiling cap, rewarding budget headroom.
- **`preferred_attributes_weight` (0.25)**: Fraction of optional requested attributes matched.
- **`preferred_brands_weight` (0.15)**: Brand match against user's preferred brand list.
- **`preferred_retailers_weight` (0.15)**: Domain match against user's preferred merchant list.
- **`condition_weight` (0.05)**: Full score for brand-new condition.
- **`data_quality_weight` (0.05)**: Completeness of imagery and product description.

### Deterministic Tie-Breaking
When two candidates share identical scores:
1. **Lower Price**: Cheaper offer ranks first.
2. **Positive Matching Factors**: Higher number of confirmed advantages ranks first.
3. **Alphabetical ID**: `f"{product_id}:{offer_key}"` for absolute deterministic reproducibility.

---

## 💬 5. Grounded Explanation Engine

Explanations are synthesized strictly from verified facts without fabricating claims:
- Explains why the top choice was selected (e.g. matching attributes, price under budget, in-stock).
- Explains why the runner-up or key alternatives were rejected or ranked lower.
- Identifies any catalog data uncertainties.
- Disallows claims of "best" unless backed by evidence; never claims final purchase authorization.

---

## 🔌 6. Integration Guide (Zero-Modification)

B7 is packaged as a standalone isolated module and can be consumed by other services via dependency injection:

```python
from decimal import Decimal
from modules.b7_candidate_ranking import (
    ComparisonService,
    ShoppingRequest,
    MandateSnapshot,
    RankingConfig,
)
from modules.b6_channel3 import NormalizedProduct

# 1. Adapt B6 products to B7 candidate options
candidate_options = []
for b6_prod in b6_products:
    candidate_options.extend(ComparisonService.adapt_b6_product(b6_prod))

# 2. Define shopping request and spending mandate
request = ShoppingRequest(
    original_text="Looking for a warm LED desk lamp under $50",
    max_price=Decimal("50.00"),
    currency="USD",
    required_attributes={"type": "desk"},
    preferred_brands=["Lumina"],
)

mandate = MandateSnapshot(
    per_item_cap=Decimal("60.00"),
    currency="USD",
    allowed_retailers=["target.com", "bestbuy.com"],
)

# 3. Compare and rank
service = ComparisonService()
result = service.compare_and_rank(request=request, candidates=candidate_options, mandate=mandate)

print(f"Top Choice: {result.selected_candidate.product_title}")
print(f"Explanation: {result.explanation}")
```

---

## 🧪 7. Running Tests

Execute the comprehensive test suite in isolated read-only mode:

```bash
python3 -m pytest modules/b7_candidate_ranking/tests -v
```
