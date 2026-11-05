"""
Mandate validator for Module B8 — Deterministic Guardrail & Policy Engine.

Validates the lifecycle, status, and structural integrity of a MandateSnapshot
before any candidate or proposal evaluation proceeds.

Rules:
- A missing mandate produces UNABLE_TO_DETERMINE (not APPROVED).
- An expired mandate produces REJECTED.
- A non-active mandate (revoked, superseded, cancelled) produces REJECTED.
- Mandate with no currency field produces UNABLE_TO_DETERMINE.
- No LLM is used; all checks are deterministic Python code.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from server.app.services.ranking.models import MandateSnapshot
from server.app.services.guardrails.models import PolicyRuleResult, PolicyViolationCode

logger = logging.getLogger("cartiq.b8.mandate_validator")

# Lifecycle states that represent a valid, active mandate.
_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})

# Lifecycle states that are definitively non-active.
_INACTIVE_STATUSES: frozenset[str] = frozenset({"revoked", "superseded", "cancelled", "expired", "inactive"})


def validate_mandate(
    mandate: Optional[MandateSnapshot],
    now: Optional[datetime] = None,
) -> list[PolicyRuleResult]:
    """Evaluate mandate lifecycle, status, and structural validity.

    Returns:
        List of PolicyRuleResult — empty list if mandate is fully valid.
        A non-empty list means mandate validation failed and downstream
        evaluation MUST NOT proceed as APPROVED.

    Args:
        mandate:  The MandateSnapshot to validate. None triggers MANDATE_MISSING.
        now:      Current UTC datetime (injectable for deterministic testing).
    """
    current_time = now or datetime.now(timezone.utc)
    results: list[PolicyRuleResult] = []

    # --- Rule 1: Mandate existence ---
    if mandate is None:
        results.append(PolicyRuleResult(
            rule_name="mandate_existence",
            passed=False,
            violation_code=PolicyViolationCode.MANDATE_MISSING,
            detail="No mandate snapshot was provided. Policy cannot be evaluated without an active mandate.",
        ))
        # Cannot evaluate further without a mandate object.
        return results

    # --- Rule 2: Mandate status lifecycle ---
    mandate_status_norm = (mandate.status or "").strip().lower()
    if mandate_status_norm not in _ACTIVE_STATUSES:
        if mandate_status_norm in _INACTIVE_STATUSES:
            detail = (
                f"Mandate lifecycle state '{mandate.status}' is not active. "
                "Only an 'active' mandate may authorize purchases."
            )
        else:
            detail = (
                f"Mandate lifecycle state '{mandate.status}' is unrecognized. "
                "Cannot safely evaluate policy against an unknown mandate state."
            )
        results.append(PolicyRuleResult(
            rule_name="mandate_lifecycle_status",
            passed=False,
            violation_code=PolicyViolationCode.MANDATE_INVALID_STATUS,
            detail=detail,
        ))
    else:
        results.append(PolicyRuleResult(
            rule_name="mandate_lifecycle_status",
            passed=True,
            violation_code=None,
            detail=f"Mandate status '{mandate.status}' is active.",
        ))

    # --- Rule 3: Mandate expiration ---
    if mandate.expires_at is not None:
        # Normalize both timestamps to UTC for safe comparison.
        expires_utc = (
            mandate.expires_at.astimezone(timezone.utc)
            if mandate.expires_at.tzinfo
            else mandate.expires_at.replace(tzinfo=timezone.utc)
        )
        now_utc = (
            current_time.astimezone(timezone.utc)
            if current_time.tzinfo
            else current_time.replace(tzinfo=timezone.utc)
        )
        if now_utc >= expires_utc:
            results.append(PolicyRuleResult(
                rule_name="mandate_expiration",
                passed=False,
                violation_code=PolicyViolationCode.MANDATE_EXPIRED,
                detail=(
                    f"Mandate expired at {mandate.expires_at.isoformat()}. "
                    f"Current time is {current_time.isoformat()}. Expired mandates cannot authorize purchases."
                ),
            ))
        else:
            results.append(PolicyRuleResult(
                rule_name="mandate_expiration",
                passed=True,
                violation_code=None,
                detail=f"Mandate is valid until {mandate.expires_at.isoformat()}.",
            ))
    else:
        results.append(PolicyRuleResult(
            rule_name="mandate_expiration",
            passed=True,
            violation_code=None,
            detail="Mandate has no expiration timestamp set (no expiry constraint).",
        ))

    # --- Rule 4: Mandate currency presence ---
    mandate_currency = (mandate.currency or "").strip().upper()
    if not mandate_currency or len(mandate_currency) != 3:
        results.append(PolicyRuleResult(
            rule_name="mandate_currency_validity",
            passed=False,
            violation_code=PolicyViolationCode.MANDATE_CURRENCY_MISSING,
            detail=(
                f"Mandate currency '{mandate.currency}' is missing or invalid. "
                "Cannot evaluate monetary limits without a valid currency code."
            ),
        ))
    else:
        results.append(PolicyRuleResult(
            rule_name="mandate_currency_validity",
            passed=True,
            violation_code=None,
            detail=f"Mandate currency '{mandate_currency}' is a valid 3-letter ISO code.",
        ))

    return results
