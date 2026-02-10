"""
Clerk webhook endpoints.
Handles user synchronization with Clerk authentication service.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import CurrentSession
from app.domains.users.service import ClerkUserService

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    session: CurrentSession,
):
    """
    Handle Clerk webhook events.
    Processes user.created, user.updated, and user.deleted events.
    """
    try:
        payload = await request.json()
        event_type = payload.get("type")
        data = payload.get("data", {})

        clerk_service = ClerkUserService.for_system(session)

        if event_type == "user.created":
            await clerk_service.create_user(data)
        elif event_type == "user.updated":
            await clerk_service.update_user(data)
        elif event_type == "user.deleted":
            await clerk_service.delete_user(data)
        else:
            log.info(f"Unhandled Clerk event type: {event_type}")

        return {"status": "ok"}

    except ValueError as e:
        log.error(f"Invalid Clerk webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Error processing Clerk webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
