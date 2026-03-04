"""
Logfire observability configuration.
Centralizes Logfire setup and all instrumentation.

Pydantic validation is instrumented statically via [tool.logfire] in pyproject.toml.
Dynamic instrumentations (SQLAlchemy, FastAPI) are applied here after configure().
"""

import logfire
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.config import Settings


def configure_logfire(settings: Settings) -> None:
    """Configure Logfire. Must be called before any instrumentation."""
    logfire.configure(
        service_name=settings.LOGFIRE_SERVICE_NAME,
        send_to_logfire=settings.LOGFIRE_SEND_TO_LOGFIRE,
    )


def instrument_app(app: FastAPI, engine: AsyncEngine) -> None:
    """Instrument FastAPI and SQLAlchemy after Logfire is configured."""
    logfire.instrument_fastapi(app)
    logfire.instrument_sqlalchemy(engine)
