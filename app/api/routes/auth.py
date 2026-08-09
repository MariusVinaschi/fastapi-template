"""
Authentication endpoints: login, refresh, logout.

Handlers stay thin: credential checks live in ``UserService.authenticate``, refresh-token
authentication in ``VerifyAuth.get_refresh_auth`` (via ``CurrentRefreshAuth``), and all
token/cookie issuance in ``app.api.tokens``. The request-scoped commit is owned by
``get_session``; the single explicit commit here persists a security-critical side-effect
(refresh-token family revocation) that must survive the 401 response.
"""

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api import tokens
from app.api.dependencies import CurrentRefreshAuth, CurrentSession
from app.api.rate_limit import limiter
from app.domains.base.schemas import Status
from app.domains.sessions.exceptions import InvalidRefreshTokenError, RefreshTokenReuseError
from app.domains.users.exceptions import InvalidCredentialsError
from app.domains.users.schemas import TokenPair, UserLogin
from app.domains.users.service import UserService

router = APIRouter()

INVALID_CREDENTIALS = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
INVALID_REFRESH = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.post("/login", response_model=None)
@limiter.limit("5/minute")
async def login(
    request: Request, payload: UserLogin, session: CurrentSession, response: Response
) -> TokenPair | Status:
    """Authenticate with email + password and issue tokens."""
    try:
        user = await UserService.for_system(session).authenticate(payload.email, payload.password)
    except InvalidCredentialsError as e:
        raise INVALID_CREDENTIALS from e

    return await tokens.issue_pair(user, session, response)


@router.post("/refresh", response_model=None)
@limiter.limit("10/minute")
async def refresh(
    request: Request, refresh_auth: CurrentRefreshAuth, session: CurrentSession, response: Response
) -> TokenPair | Status:
    """Exchange a valid refresh token for a new pair (with rotation + reuse detection)."""
    try:
        return await tokens.rotate_pair(refresh_auth.token, refresh_auth.user, session, response)
    except RefreshTokenReuseError as e:
        # The family revocation must persist even though we reject this request, so commit
        # before the raised error triggers the request-scoped rollback in get_session.
        await session.commit()
        tokens.clear_cookies(response)
        raise INVALID_REFRESH from e
    except InvalidRefreshTokenError as e:
        tokens.clear_cookies(response)
        raise INVALID_REFRESH from e


@router.post("/logout")
async def logout(refresh_auth: CurrentRefreshAuth, session: CurrentSession, response: Response) -> Status:
    """Revoke the current refresh token family and clear cookies (authenticated by refresh token)."""
    await tokens.revoke(refresh_auth.token, refresh_auth.user, session)
    tokens.clear_cookies(response)
    return Status(detail="Successfully logged out")
