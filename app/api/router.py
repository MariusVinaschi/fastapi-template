"""
API router configuration.
Aggregates all route modules into the main routers.
"""

from fastapi.routing import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.users import router as users_router, me_router
from app.api.routes.webhooks.clerk import router as clerk_webhook_router

# Main API router - version prefixed
api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(me_router, prefix="/me", tags=["me"])
api_router.include_router(health_router, prefix="/health", tags=["health"])

# Webhook router - separate from versioned API
webhook_router = APIRouter()
webhook_router.include_router(clerk_webhook_router)
