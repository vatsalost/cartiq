"""PayPal Webhook schemas."""

from pydantic import BaseModel


class PayPalWebhookResponse(BaseModel):
    """Acknowledgement of PayPal webhook delivery."""

    status: str = "success"
    event_id: str
