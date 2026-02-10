"""
Health check endpoints.
"""

from fastapi.routing import APIRouter

from app.infrastructure.config import settings

router = APIRouter()


@router.get("/")
async def health():
    """
    Health check endpoint.
    Returns the current health status and testing mode.
    """
    return {"health": "UP", "testing": settings.TESTING}
