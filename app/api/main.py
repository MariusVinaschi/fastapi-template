"""
FastAPI application factory and configuration.
This is the entry point for the HTTP API.
"""

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.rate_limit import limiter
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

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # CORS must be added before SlowAPI: Starlette applies middleware in reverse
    # registration order, so the last-added runs first. CORS must run outermost so
    # that rate-limited 429 responses still include the correct CORS headers and
    # browsers don't misreport them as CORS errors.
    add_cors_middleware(application, settings)
    application.add_middleware(SlowAPIMiddleware)  # type: ignore[arg-type]

    application.include_router(router=api_router, prefix=settings.API_V1_STR)
    application.include_router(router=webhook_router, prefix="/webhooks", tags=["webhooks"])
    instrument_app(application, async_engine)

    return application


# Create the application instance
app = create_application()
