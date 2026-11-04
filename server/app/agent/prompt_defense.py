"""Prompt injection defense, delimiter framing, and log sanitization (Module B5)."""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

# Common prompt injection, jailbreak, and privilege escalation patterns
INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|system)\s+instructions\b",
    r"(?i)\breveal\s+(your\s+)?(system\s+prompt|instructions|internal\s+rules)\b",
    r"(?i)\bprint\s+(your\s+)?(system\s+prompt|developer\s+instructions)\b",
    r"(?i)\b(developer|debug|god|unrestricted)\s+mode\b",
    r"(?i)\b(jailbreak|dan\s+mode|bypass\s+safety)\b",
    r"(?i)\b(create_paypal_order|capture_payment|refund_payment|execute_checkout)\b",
    r"(?i)\b(paypal\s+api|access\s+paypal|charge\s+card|send\s+payment)\b",
    r"(?i)\b(change|modify|increase|bypass|override)\s+.*?(budget|mandate|limit)\b",
    r"(?i)\b(drop\s+table|delete\s+from|insert\s+into|union\s+select)\b",
    r"(?i)\b(eval\(|exec\(|subprocess|system\()\b",
    r"(?i)<\s*script[^>]*>.*?</\s*script\s*>",
]

SENSITIVE_KEY_PATTERNS = [
    r"api[-_]?key",
    r"secret",
    r"token",
    r"password",
    r"bearer",
    r"authorization",
    r"credit[-_]?card",
    r"private[-_]?key",
    r"session",
]

COMPILED_INJECTION_RE = [re.compile(p) for p in INJECTION_PATTERNS]
COMPILED_SENSITIVE_RE = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_KEY_PATTERNS]


class PromptDefense:
    """Security utilities for untrusted input framing, threat detection, and log sanitization."""

    @staticmethod
    def wrap_user_input(text: str) -> str:
        """Enclose user input inside explicit boundary delimiters."""
        clean_text = PromptDefense.strip_control_characters(text)
        return f"<<<UNTRUSTED_USER_REQUEST_START>>>\n{clean_text}\n<<<UNTRUSTED_USER_REQUEST_END>>>"

    @staticmethod
    def wrap_catalog_data(data: Any) -> str:
        """Enclose external product or retailer data in untrusted catalog delimiters."""
        return f"<<<UNTRUSTED_CATALOG_DATA_START>>>\n{data}\n<<<UNTRUSTED_CATALOG_DATA_END>>>"

    @staticmethod
    def strip_control_characters(text: str) -> str:
        """Remove null bytes, Bidi overrides, and unprintable control characters."""
        if not text:
            return ""
        # Remove null bytes and unicode directional formatting characters
        text = text.replace("\x00", "")
        # Remove common RTL/LTR overrides used for prompt spoofing
        for c in ["\u202A", "\u202B", "\u202C", "\u202D", "\u202E", "\u2066", "\u2067", "\u2068", "\u2069"]:
            text = text.replace(c, "")
        return text

    @staticmethod
    def detect_injection_patterns(text: str) -> Tuple[bool, Optional[str]]:
        """Scan input for obvious prompt injection, jailbreaks, or privilege escalation.
        
        Returns (is_threat, detected_reason).
        """
        if not text:
            return False, None

        for pattern in COMPILED_INJECTION_RE:
            match = pattern.search(text)
            if match:
                return True, f"Detected adversarial pattern: '{match.group(0)}'"

        return False, None

    @staticmethod
    def sanitize_log_data(data: Any) -> Any:
        """Recursively redact secrets, credentials, tokens, and passwords from logs."""
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                is_sensitive = any(p.search(str(k)) for p in COMPILED_SENSITIVE_RE)
                if is_sensitive:
                    sanitized[k] = "***REDACTED***"
                else:
                    sanitized[k] = PromptDefense.sanitize_log_data(v)
            return sanitized
        elif isinstance(data, list):
            return [PromptDefense.sanitize_log_data(item) for item in data]
        elif isinstance(data, str):
            # Check for JWT / Bearer tokens or hex secrets
            if data.startswith("Bearer ") or data.startswith("ghp_") or data.startswith("AIza"):
                return "***REDACTED_TOKEN***"
            return data
        return data
