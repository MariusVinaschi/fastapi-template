"""
FastAPI application factory and configuration.
This is the entry point for the HTTP API.
"""

from fastapi import FastAPI

from app.api.router import api_router, webhook_router
from app.infrastructure.config import settings
from app.infrastructure.database import async_engine
from app.infrastructure.logging_config import setup_logging
from app.infrastructure.middleware import add_cors_middleware
from app.infrastructure.observability import configure_logfire, instrument_app


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This is the main factory function for the API.

    :return: Configured FastAPI application
    """
    configure_logfire(settings)
    setup_logging(settings)

    application = FastAPI(
        title="FastAPI Template",
        version=settings.VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
    )

    application.include_router(router=api_router, prefix=settings.API_V1_STR)
    application.include_router(router=webhook_router, prefix="/webhooks", tags=["webhooks"])

    add_cors_middleware(application, settings)
    instrument_app(application, async_engine)

    return application


# Create the application instance
app = create_application()
