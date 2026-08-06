"""
AuthX integration - the JWT engine for access/refresh tokens.

Builds a single ``security`` instance from application settings. Token transport
(headers / cookies) and CSRF protection are driven entirely by config so consuming
apps flip behaviour without code changes:

- ``AUTH_TOKEN_LOCATION=headers``          -> Bearer tokens (SPA/mobile/CLI), no CSRF
- ``AUTH_TOKEN_LOCATION=cookies``          -> HttpOnly cookies + CSRF double-submit
- ``AUTH_TOKEN_LOCATION=headers,cookies``  -> both accepted; CSRF enforced on cookie writes

The token subject (``sub``) is the user's UUID (as a string).
"""

from datetime import timedelta
from typing import Literal, cast

from authx import AuthX, AuthXConfig
from authx.types import TokenLocations

from app.infrastructure.config import settings

_config = AuthXConfig(
    JWT_SECRET_KEY=settings.AUTH_JWT_SIGNING_KEY,
    JWT_TOKEN_LOCATION=cast(TokenLocations, settings.AUTH_TOKEN_LOCATIONS),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRES_MINUTES),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=settings.AUTH_REFRESH_TOKEN_EXPIRES_DAYS),
    JWT_COOKIE_CSRF_PROTECT=settings.AUTH_COOKIE_CSRF_PROTECT,
    JWT_COOKIE_SECURE=settings.AUTH_COOKIE_SECURE,
    JWT_COOKIE_SAMESITE=cast(Literal["lax", "strict", "none"], settings.AUTH_COOKIE_SAMESITE),
)

security = AuthX(config=_config)
