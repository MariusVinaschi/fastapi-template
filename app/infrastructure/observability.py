"""
Logfire observability configuration.
Centralizes Logfire setup and FastAPI instrumentation.
"""

import logfire
from fastapi import FastAPI

from app.infrastructure.config import Settings


def configure_logfire(settings: Settings) -> None:
    """
    Configure Logfire (service name, send flag) and instrument Pydantic.
    Must be called first in application bootstrap, before any code that uses logfire.
    """
    logfire.configure(
        service_name=settings.LOGFIRE_SERVICE_NAME,
        send_to_logfire=settings.LOGFIRE_SEND_TO_LOGFIRE,
    )
    logfire.instrument_pydantic(exclude={"app.infrastructure.config"})


def instrument_app(app: FastAPI) -> None:
    """Instrument the FastAPI application with Logfire for request tracing."""
    logfire.instrument_fastapi(app)
