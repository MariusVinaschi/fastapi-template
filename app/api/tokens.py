"""
Token issuance orchestration for the auth delivery layer.

Bridges AuthX (JWT creation + cookies, infrastructure) with the RefreshSessionService
(domain) and the HTTP response. Kept out of the route handlers so they stay thin.

Authentication of incoming refresh requests lives in ``VerifyAuth.get_refresh_auth``
(infrastructure); this module only *issues* tokens and shapes the response.

Transport is config-driven (``AUTH_TOKEN_LOCATION``): tokens are set as HttpOnly cookies
when cookies are enabled, and returned in the JSON body only when headers are enabled
(so a pure-cookie deployment never leaks tokens into a JS-readable body).
"""

from datetime import UTC, datetime, timedelta

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.schemas import Status
from app.domains.sessions.service import RefreshSessionService
from app.domains.users.authorization import UserAuthorizationAdapter
from app.domains.users.models import User
from app.domains.users.schemas import TokenPair
from app.infrastructure.auth import security
from app.infrastructure.config import settings

# Body returned when tokens live only in cookies (no token echoed into the response body).
COOKIE_ONLY_BODY = Status(detail="Authenticated")


def _refresh_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.AUTH_REFRESH_TOKEN_EXPIRES_DAYS)


def _cookies_enabled() -> bool:
    return "cookies" in settings.AUTH_TOKEN_LOCATIONS


def _headers_enabled() -> bool:
    return "headers" in settings.AUTH_TOKEN_LOCATIONS


def _set_cookies(access_token: str, refresh_token: str, response: Response) -> None:
    if _cookies_enabled():
        security.set_access_cookies(access_token, response)
        security.set_refresh_cookies(refresh_token, response)


def clear_cookies(response: Response) -> None:
    security.unset_cookies(response)


def _response_body(access_token: str, refresh_token: str) -> TokenPair | Status:
    if _headers_enabled():
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
    return COOKIE_ONLY_BODY


async def issue_pair(user: User, session: AsyncSession, response: Response) -> TokenPair | Status:
    """Mint an access+refresh pair for a user, persist the refresh session, set cookies."""
    context = UserAuthorizationAdapter(user)
    access_token = security.create_access_token(uid=str(user.id))
    refresh_token = security.create_refresh_token(uid=str(user.id))
    await RefreshSessionService.for_user(session, context).issue(user.id, refresh_token, _refresh_expiry())
    _set_cookies(access_token, refresh_token, response)
    return _response_body(access_token, refresh_token)


async def rotate_pair(
    raw_refresh_token: str,
    user: User,
    session: AsyncSession,
    response: Response,
) -> TokenPair | Status:
    """Rotate the presented refresh token for a new pair (reuse detection in the service)."""
    context = UserAuthorizationAdapter(user)
    new_access = security.create_access_token(uid=str(user.id))
    new_refresh = security.create_refresh_token(uid=str(user.id))
    await RefreshSessionService.for_user(session, context).rotate(
        old_refresh_token=raw_refresh_token,
        new_refresh_token=new_refresh,
        expires_at=_refresh_expiry(),
    )
    _set_cookies(new_access, new_refresh, response)
    return _response_body(new_access, new_refresh)


async def revoke(raw_refresh_token: str, user: User, session: AsyncSession) -> None:
    """Revoke the refresh token's family (logout)."""
    context = UserAuthorizationAdapter(user)
    await RefreshSessionService.for_user(session, context).revoke(raw_refresh_token)
