"""PayPal asynchronous webhook receiver."""

import json
from fastapi import APIRouter, Depends, Request, status
from server.app.api.dependencies import get_webhook_service
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.schemas.webhook import PayPalWebhookResponse
from server.app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/paypal",
    response_model=PayPalWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Receive and reconcile PayPal webhook events",
    description="Validates signature, deduplicates provider events, and updates order states monotonically.",
)
async def receive_paypal_webhook(
    request: Request,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except Exception:
        raise CartiAPIException(
            code=CartiErrorCode.VALIDATION_ERROR,
            message="Malformed JSON in webhook request body.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    headers_dict = dict(request.headers)
    success, event_id = webhook_service.process_webhook(
        headers=headers_dict,
        raw_body=raw_body,
        payload=payload,
    )
    return PayPalWebhookResponse(status="success", event_id=event_id)
