"""
HTTP middleware configuration.
Registers CORS and other middlewares on the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config import Settings

_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_ALLOWED_HEADERS = ["Authorization", "Content-Type", "X-API-Key"]


def add_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """Add CORS middleware to the application using allowed origins from settings."""
    origins = settings.ALLOWED_CORS_ORIGINS

    if "*" in origins:
        raise ValueError(
            "CORS_ORIGINS must not contain '*' when credentials are enabled. Set explicit origins instead."
        )

    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )
