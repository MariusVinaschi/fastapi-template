"""
FastAPI application factory and configuration.
This is the entry point for the HTTP API.
"""

import logging
import sys
from pathlib import Path

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, webhook_router

# Import all models to ensure they are registered with SQLAlchemy
# This must be done before creating the FastAPI app to avoid circular import issues
from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This is the main factory function for the API.

    :return: Configured FastAPI application
    """
    # Observability: Pydantic Logfire (configure first so logging handler can use it)
    logfire.configure(
        service_name=settings.LOGFIRE_SERVICE_NAME,
        send_to_logfire=settings.LOGFIRE_SEND_TO_LOGFIRE,
    )

    # Logging: local (console + file) + Logfire
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    Path("logs").mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log"),
        logfire.LogfireLoggingHandler(),
    ]
    for h in handlers:
        h.setFormatter(logging.Formatter(log_format))
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

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
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.ALLOWED_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logfire.instrument_fastapi(application)

    return application


# Create the application instance
app = create_application()
