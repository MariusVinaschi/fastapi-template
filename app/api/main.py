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
    if not settings.CLERK_FRONTEND_API_URL.strip():
        # Fail fast here rather than in Settings: PyJWKClient only fetches the JWKS URL
        # lazily on first use, so an empty CLERK_FRONTEND_API_URL would otherwise start
        # up "healthy" and only fail confusingly on the first JWT-authenticated request.
        # Scoped to the API entrypoint (not Settings itself) since the worker and
        # migrations images also import Settings but never call create_application()
        # and don't need Clerk configured.
        raise ValueError(
            "CLERK_FRONTEND_API_URL must be set to a valid Clerk Frontend API URL "
            "(e.g. https://your-app.clerk.accounts.dev)."
        )

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

    add_cors_middleware(application, settings)
    application.add_middleware(SlowAPIMiddleware)  # type: ignore[arg-type]

    application.include_router(router=api_router, prefix=settings.API_V1_STR)
    application.include_router(router=webhook_router, prefix="/webhooks", tags=["webhooks"])
    instrument_app(application, async_engine)

    return application


# Create the application instance
app = create_application()
