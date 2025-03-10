from fastapi.routing import APIRouter

from app.config import settings

from app.user.router import me_router
from app.user.router import router as users_router

health_router = APIRouter()


@health_router.get("/")
async def health():
    return {"health": "UP", "testing": settings.TESTING}


api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(me_router, prefix="/me", tags=["me"])

