# 🛡️ Module B8: Deterministic Guardrail & Policy Engine

Part of the **CartiQ Agentic Shopping Concierge**.

---

## 1. Module Overview

Module B8 is the **authoritative, server-side policy engine** for CartiQ. It
deterministically evaluates whether a proposed shopping action satisfies the
active user mandate, spending limits, category restrictions, retailer
constraints, and all other hard policy rules before any purchase proposal
may proceed.

```
[B7: Candidate Ranking & Explanation]
         │ (RankedCandidate / ProposalEvaluationRequest)
         ▼
┌──────────────────────────────────────────────────────────────┐
│  MODULE B8: DETERMINISTIC GUARDRAIL & POLICY ENGINE          │
│                                                              │
│  Phase 1 — Mandate Lifecycle Validation                      │
│    • Mandate existence (MANDATE_MISSING)                     │
│    • Mandate status (active / revoked / superseded / …)      │
│    • Mandate expiration timestamp                            │
│    • Mandate currency validity                               │
│                                                              │
│  Phase 2 — Offer & Product Structural Validity               │
│    • Product ID and title presence                           │
│    • Offer key, domain, and buy URL presence                 │
│    • Price validity (> 0, Decimal)                           │
│                                                              │
│  Phase 3 — Stock Availability                                │
│    • InStock confirmation (unknown ≠ in-stock)               │
│                                                              │
│  Phase 4 — Currency Consistency                              │
│    • Exact ISO-4217 match; no silent conversion              │
│                                                              │
│  Phase 5 — Spending Limits                                   │
│    • Total budget ceiling                                    │
│    • Per-item cap                                            │
│                                                              │
│  Phase 6 — Category Restrictions                             │
│    • Blocked categories (deny list)                          │
│    • Allowed categories (allow list)                         │
│                                                              │
│  Phase 7 — Retailer Allowlist                                │
│    • Domain normalized, case-insensitive                     │
│                                                              │
│  Phase 8 — Quantity Restriction                              │
│    • max_quantity ceiling                                    │
│                                                              │
│  Phase 9 — Price Tolerance Drift (checkout re-validation)    │
│    • Optional; compares against reference_price              │
│                                                              │
│  → Produces: immutable PolicyDecision                        │
└──────────────────────────────────────────────────────────────┘
         │ (PolicyDecision — authoritative, immutable)
         ▼
[B9: Proposal Service]  →  PayPal Checkout (B10/B11)
```

> [!IMPORTANT]
> **B7 ranking scores never override B8 policy decisions.** A score of 1.0
> from B7 carries zero weight in B8. The same applies to any LLM output —
> B8 is 100% deterministic Python; no AI model is authoritative here.

---

## 2. Decision States

| Status | Meaning | B9 May Proceed? |
|---|---|---|
| `APPROVED` | All rules passed | ✅ Yes |
| `REJECTED` | One or more hard rule violations | ❌ No |
| `INVALID_INPUT` | Structurally missing/invalid offer or product data | ❌ No |
| `UNABLE_TO_DETERMINE` | Mandate missing; cannot safely evaluate | ❌ No |

**Rule:** `decision.is_safe_to_proceed` returns `True` only for `APPROVED`.
B9 must check this property and must not proceed with any other status.

---

## 3. Policy Violation Codes

| Code | Trigger |
|---|---|
| `MANDATE_MISSING` | No mandate provided |
| `MANDATE_EXPIRED` | Mandate expiration timestamp elapsed |
| `MANDATE_INVALID_STATUS` | Status is not `active` |
| `MANDATE_CURRENCY_MISSING` | Mandate currency absent or invalid |
| `BUDGET_EXCEEDED` | Offer price > `total_budget` |
| `PER_ITEM_CAP_EXCEEDED` | Offer price > `per_item_cap` |
| `BLOCKED_CATEGORY` | Category matches mandate blocked list |
| `CATEGORY_NOT_ALLOWED` | Category not in mandate allowed list |
| `RETAILER_NOT_ALLOWED` | Domain not in mandate allowed retailers |
| `QUANTITY_EXCEEDED` | Requested quantity > `max_quantity` |
| `CURRENCY_MISMATCH` | Offer currency ≠ mandate currency |
| `INVALID_PRICE` | Price is zero, negative, or missing |
| `OUT_OF_STOCK` | Availability not confirmed in-stock |
| `INVALID_OFFER_DATA` | Missing offer_key, domain, or buy_url |
| `INVALID_PRODUCT_DATA` | Missing product_id or title |
| `PRICE_TOLERANCE_EXCEEDED` | Price drifted beyond `price_tolerance` from reference |

---

## 4. Input Contract (from B9)

```python
from modules.b8_guardrail_policy.models import ProposalEvaluationRequest
from decimal import Decimal

proposal = ProposalEvaluationRequest(
    candidate_id="prod_001:off_target_1",
    product_id="prod_001",
    offer_key="off_target_1",
    product_title="Lumina LED Desk Lamp",
    category="Home Lighting",
    domain="target.com",
    buy_url="https://buy.trychannel3.com/target/1",
    price_amount=Decimal("34.99"),
    currency="USD",
    availability="InStock",
    condition="new",
    quantity=1,
    # B7 ranking score — provided for reference/logging ONLY.
    # B8 ignores it completely in policy evaluation.
    b7_ranking_score=0.87,
)
```

The `MandateSnapshot` is consumed from B7's existing model (read-only).

---

## 5. Output Contract (PolicyDecision — consumed by B9)

```python
from modules.b8_guardrail_policy import DecisionService

svc = DecisionService()
decision = svc.evaluate(proposal=proposal, mandate=mandate_snapshot)

# B9 MUST check this before any checkout action:
if not decision.is_safe_to_proceed:
    raise PolicyRejectionError(decision.rejection_reasons)

# Full audit trail available:
for rule in decision.rule_results:
    print(f"{rule.rule_name}: {'PASS' if rule.passed else 'FAIL'} — {rule.detail}")
```

**PolicyDecision fields:**

| Field | Type | Description |
|---|---|---|
| `decision_id` | `str` (UUID) | Unique evaluation identifier |
| `status` | `PolicyDecisionStatus` | Authoritative outcome |
| `candidate_id` | `Optional[str]` | Evaluated candidate |
| `offer_key` | `Optional[str]` | Evaluated offer |
| `rule_results` | `list[PolicyRuleResult]` | Full traceable rule audit |
| `violations` | `list[PolicyViolationCode]` | All failed rule codes |
| `rejection_reasons` | `list[str]` | Human-readable reason strings |
| `evaluated_price` | `Optional[Decimal]` | Offer price evaluated |
| `evaluated_currency` | `Optional[str]` | Currency evaluated |
| `evaluated_quantity` | `Optional[int]` | Quantity evaluated |
| `mandate_status_at_evaluation` | `Optional[str]` | Mandate status captured |
| `evaluated_at` | `datetime` | UTC timestamp of evaluation |
| `is_safe_to_proceed` | `bool` | True only if APPROVED |
| `is_approved` | `bool` | Convenience alias |
| `is_rejected` | `bool` | Convenience alias |

> [!CAUTION]
> `PolicyDecision` is **frozen** (immutable). Any downstream module that attempts
> to mutate it will receive a `ValidationError`. Downstream modules must never
> reconstruct or fake a `PolicyDecision`.

---

## 6. How B7 Communicates with B8

B7 produces `RankedCandidate` and `ComparisonResult`. B9 (or the agent
orchestrator) maps the top `RankedCandidate` into a `ProposalEvaluationRequest`
and submits it to B8:

```python
from modules.b8_guardrail_policy.models import ProposalEvaluationRequest
from modules.b8_guardrail_policy import DecisionService

# ranked is a B7 RankedCandidate
proposal = ProposalEvaluationRequest(
    candidate_id=ranked.candidate_id,
    product_id=ranked.product_id,
    offer_key=ranked.offer_key,
    product_title=ranked.product_title,
    category=ranked.category,
    domain=ranked.domain,
    buy_url=ranked.buy_url,
    price_amount=ranked.price_amount,
    currency=ranked.currency,
    availability=ranked.availability,
    condition=ranked.condition,
    b7_ranking_score=ranked.ranking_score,  # reference only; never authoritative
)

decision = DecisionService().evaluate(proposal=proposal, mandate=mandate)
```

**B7 eligibility ≠ B8 authorization.** A candidate passing B7's
`EligibilityFilter` is merely ranked; it still requires B8 approval before
any purchase action.

---

## 7. How B9 Consumes B8 Decisions

B9 must:
1. Submit a `ProposalEvaluationRequest` to `DecisionService.evaluate()`.
2. Check `decision.is_safe_to_proceed` before any budget reservation.
3. If `False`, surface `decision.rejection_reasons` to the user and halt.
4. Store `decision.decision_id` for audit trail purposes.
5. Never call PayPal APIs (B10/B11) unless B8 returns `APPROVED`.

B9 must **never**:
- Treat `REJECTED`, `INVALID_INPUT`, or `UNABLE_TO_DETERMINE` as approved.
- Re-evaluate policy itself or use B7 scores as authorization.
- Skip B8 evaluation for "trusted" or "pre-approved" candidates.

---

## 8. Security Design

| Threat | Mitigation |
|---|---|
| LLM approval bypass | B8 has no API accepting LLM verdicts; all decisions are deterministic code |
| Browser/client price injection | Prices come from `ProposalEvaluationRequest` (server-constructed, not client-supplied) |
| B7 score override | `b7_ranking_score` is logged only; engine ignores it |
| Silent currency conversion | `rule_currency_consistent` enforces exact match; no conversion ever performed |
| Downstream rejection bypass | `PolicyDecision` is Pydantic-frozen; mutation raises `ValidationError` |
| Product description injection | Descriptions are never executed or used in policy logic |
| Payment execution | B8 contains zero PayPal primitives; no credentials, no captures, no refunds |
| Missing mandate silent pass | Missing mandate → `UNABLE_TO_DETERMINE`; never `APPROVED` |

---

## 9. Running Isolated B8 Tests

Execute only B8 tests without touching other modules:

```bash
cd /path/to/cartiq
python3 -m pytest modules/b8_guardrail_policy/tests -v
```

The test suite is fully isolated:
- Uses only mock fixtures defined in `tests/conftest.py`.
- Does not modify any database, file, or shared state.
- Does not require environment variables or external services.

---

## 10. File Structure

```
modules/b8_guardrail_policy/
├── __init__.py              # Public API exports
├── models.py                # PolicyDecision, ProposalEvaluationRequest, enums
├── exceptions.py            # B8Error hierarchy
├── mandate_validator.py     # Phase 1: Mandate lifecycle checks
├── policy_rules.py          # Individual deterministic rule functions
├── eligibility_engine.py    # Orchestrates all rule phases
├── decision_service.py      # Top-level DecisionService (public entry point)
├── README.md                # This document
└── tests/
    ├── __init__.py
    ├── conftest.py          # Fixtures and factories
    └── test_policy_engine.py  # 40+ test cases
```

---

## 11. Known Limitations & Integration Requirements

### Limitations

1. **Available Budget Runtime Check**: B8's `rule_budget_not_exceeded` checks
   the offer price against the mandate's declared `total_budget` ceiling. The
   real-time *available* budget (after deducting captured spend and active
   reservations) is a database-state concern that must be enforced at the
   checkout layer (B9/B3) using row-level locking. B8 does not access the
   database.

2. **Mandate Snapshot Currency**: B8 consumes the `MandateSnapshot.currency`
   field. If the caller passes a stale or incorrect snapshot, B8 will evaluate
   against stale data. B9 is responsible for fetching the current mandate.

3. **No Quantity × Price Check**: B8 validates `quantity ≤ max_quantity` and
   `price ≤ per_item_cap/total_budget` independently. It does not compute
   `quantity × price` vs. available budget (this is a runtime reservation concern).

### Integration Requirements (Without Existing File Modification)

The following integrations are **required** but cannot be completed by B8
itself without modifying existing files (which is prohibited):

| Requirement | Blocker | Recommended Adapter |
|---|---|---|
| B9 must call `DecisionService.evaluate()` before PayPal | B9 file must be modified | B9 owner adds `from modules.b8_guardrail_policy import DecisionService` |
| Agent orchestrator must pass mandate snapshot to B8 | Agent file must be modified | Agent owner injects MandateSnapshot from B3 into B8 call |
| Available-budget enforcement after B8 approval | Requires DB + B3 integration at B9 | B9 owner runs B3 reservation after B8 APPROVED decision |

> [!NOTE]
> Zero modifications were made to any pre-existing files.
> B8 is fully self-contained and ready to be consumed by modifying B9.
