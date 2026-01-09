"""
FastAPI application factory and configuration.
This is the entry point for the HTTP API.
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models to ensure they are registered with SQLAlchemy
# This must be done before creating the FastAPI app to avoid circular import issues
import app.models  # noqa: F401
from app.infrastructure.config import settings
from app.api.router import api_router, webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This is the main factory function for the API.

    :return: Configured FastAPI application
    """
    application = FastAPI(
        title="FastAPI Template",
        version=settings.VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
    )

    # Include routers
    application.include_router(router=api_router, prefix=settings.API_V1_STR)
    application.include_router(router=webhook_router, prefix="/webhooks", tags=["webhooks"])

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


# Create the application instance
app = create_application()

