"""
Logfire observability configuration.
Centralizes Logfire setup and all instrumentation.

Pydantic validation is instrumented statically via [tool.logfire] in pyproject.toml.
Dynamic instrumentations (SQLAlchemy, FastAPI) are applied here after configure().
"""

import logging

import logfire
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.config import Settings

logger = logging.getLogger(__name__)


def configure_logfire(settings: Settings) -> None:
    """Configure Logfire. Must be called before any instrumentation.

    If send_to_logfire is True but no token is set, falls back to False
    to avoid authentication errors (e.g. on CI or local dev without credentials).
    """
    send_to_logfire = settings.LOGFIRE_SEND_TO_LOGFIRE
    if send_to_logfire and not settings.LOGFIRE_TOKEN:
        logger.warning("LOGFIRE_SEND_TO_LOGFIRE=true but LOGFIRE_TOKEN is not set — disabling Logfire export.")
        send_to_logfire = False

    logfire.configure(
        service_name=settings.LOGFIRE_SERVICE_NAME,
        send_to_logfire=send_to_logfire,
    )


def instrument_app(app: FastAPI, engine: AsyncEngine) -> None:
    """Instrument FastAPI and SQLAlchemy after Logfire is configured."""
    logfire.instrument_fastapi(app)
    logfire.instrument_sqlalchemy(engine)
