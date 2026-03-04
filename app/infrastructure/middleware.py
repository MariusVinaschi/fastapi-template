"""
HTTP middleware configuration.
Registers CORS and other middlewares on the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config import Settings


def add_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """Add CORS middleware to the application using allowed origins from settings."""
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.ALLOWED_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
