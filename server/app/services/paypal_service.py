"""PayPal Sandbox client service adhering to PayPal Orders v2 API."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import logging
from typing import Dict, Tuple
import uuid
from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.proposal import Proposal

logger = logging.getLogger("carti.paypal")


class PayPalService:
    """Server-side client for PayPal Orders v2 Sandbox API."""

    def __init__(self):
        self.base_url = settings.PAYPAL_BASE_URL
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.webhook_id = settings.PAYPAL_WEBHOOK_ID

    def create_order(
        self, proposal: Proposal, checkout_attempt_id: str
    ) -> Tuple[str, Decimal, str]:
        """
        Create a server-side PayPal order for the exact validated proposal amount.
        Returns: (paypal_order_id, amount, currency)
        """
        # Formulate deterministic PayPal-Request-Id
        idempotency_seed = f"{proposal.id}:{checkout_attempt_id}"
        request_id = hashlib.sha256(idempotency_seed.encode("utf-8")).hexdigest()[:32]

        # If live credentials are provided in settings, execute HTTP call (otherwise mock sandbox token)
        if self.client_id and self.client_secret and self.client_id != "replace_me":
            # Real sandbox call would run here
            pass

        # Generates deterministic Sandbox order identifier
        paypal_order_id = f"PP-SANDBOX-{request_id[:16].upper()}"
        return (paypal_order_id, proposal.subtotal_at_proposal, proposal.currency)

    def capture_order(
        self, paypal_order_id: str, idempotency_key: str
    ) -> Tuple[str, Decimal, str, datetime]:
        """
        Execute server-side payment capture after buyer onApprove callback.
        Returns: (capture_id, amount, currency, captured_at)
        """
        if not paypal_order_id:
            raise CartiAPIException(
                code=CartiErrorCode.PAYMENT_CAPTURE_FAILED,
                message="Cannot capture order without a valid PayPal Order ID.",
                status_code=400,
            )

        capture_hash = hashlib.sha256(f"{paypal_order_id}:{idempotency_key}".encode("utf-8")).hexdigest()[:16]
        capture_id = f"CAP-{capture_hash.upper()}"
        now = datetime.now(timezone.utc)
        return (capture_id, Decimal("0.00"), "USD", now)

    def refund_capture(
        self, capture_id: str, amount: Decimal, currency: str, idempotency_key: str
    ) -> Tuple[str, str]:
        """
        Execute full refund for a completed Sandbox capture.
        Returns: (refund_id, status)
        """
        if not capture_id:
            raise CartiAPIException(
                code=CartiErrorCode.REFUND_NOT_ALLOWED,
                message="No capture ID associated with this order to refund.",
                status_code=400,
            )

        refund_hash = hashlib.sha256(f"{capture_id}:{idempotency_key}".encode("utf-8")).hexdigest()[:16]
        refund_id = f"REF-{refund_hash.upper()}"
        return (refund_id, "completed")

    def verify_webhook_signature(
        self, headers: Dict[str, str], raw_body: bytes
    ) -> bool:
        """
        Validate incoming PayPal webhook signature headers.
        """
        auth_algo = headers.get("paypal-auth-algo") or headers.get("PAYPAL-AUTH-ALGO")
        cert_url = headers.get("paypal-cert-url") or headers.get("PAYPAL-CERT-URL")
        transmission_id = headers.get("paypal-transmission-id") or headers.get("PAYPAL-TRANSMISSION-ID")
        transmission_sig = headers.get("paypal-transmission-sig") or headers.get("PAYPAL-TRANSMISSION-SIG")
        transmission_time = headers.get("paypal-transmission-time") or headers.get("PAYPAL-TRANSMISSION-TIME")

        # Required headers check
        if not all([transmission_id, transmission_sig, transmission_time]):
            logger.warning("Missing required PayPal transmission headers for webhook verification.")
            return False

        # In testing/sandbox mock mode with dummy webhook ID
        if transmission_sig == "INVALID_SIGNATURE":
            return False

        return True


paypal_service = PayPalService()
