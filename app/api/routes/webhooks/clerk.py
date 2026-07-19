"""
Clerk webhook endpoints.
Handles user synchronization with Clerk authentication service.
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from svix.webhooks import Webhook, WebhookVerificationError

from app.api.dependencies import CurrentSession
from app.infrastructure.adapters.clerk import ClerkWebhookAdapter
from app.infrastructure.config import settings

router = APIRouter()

log = logging.getLogger(__name__)


class WebhookResponse(BaseModel):
    status: str


async def _verify_webhook_signature(request: Request) -> dict:
    """Verify the Svix signature Clerk attaches to every webhook."""
    if not settings.CLERK_WEBHOOK_SECRET.strip():
        # Avoids Webhook(...) raising a raw RuntimeError below.
        raise HTTPException(status_code=503, detail="Clerk webhooks are not configured (CLERK_WEBHOOK_SECRET is empty)")

    body = await request.body()
    webhook = Webhook(settings.CLERK_WEBHOOK_SECRET)
    try:
        return webhook.verify(body, dict(request.headers))
    except WebhookVerificationError as error:
        log.warning(f"Rejected Clerk webhook with invalid signature: {error}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/clerk", response_model=WebhookResponse)
async def clerk_webhook(
    request: Request,
    session: CurrentSession,
):
    """
    Handle Clerk webhook events.
    Verifies the Svix signature, then processes user.created,
    user.updated, and user.deleted events.
    """
    payload = await _verify_webhook_signature(request)

    try:
        event_type = payload.get("type")
        data = payload.get("data", {})

        clerk_service = ClerkWebhookAdapter.for_system(session)

        if event_type == "user.created":
            await clerk_service.create_user(data)
        elif event_type == "user.updated":
            await clerk_service.update_user(data)
        elif event_type == "user.deleted":
            await clerk_service.delete_user(data)
        else:
            log.info(f"Unhandled Clerk event type: {event_type}")

        return WebhookResponse(status="ok")

    except ValueError as e:
        log.error(f"Invalid Clerk webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Error processing Clerk webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
