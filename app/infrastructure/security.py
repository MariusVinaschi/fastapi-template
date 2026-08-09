import logging
from dataclasses import dataclass
from uuid import UUID

from authx.exceptions import AuthXException, MissingTokenError
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.exceptions import APIKeyNotFoundException, UserNotFoundException
from app.domains.users.models import User
from app.domains.users.service import APIKeyService, UserService
from app.infrastructure.auth import TOKEN_LOCATIONS, security
from app.infrastructure.database import get_session

log = logging.getLogger(__name__)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403"""
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class RefreshTokenAuth:
    """Result of authenticating a request by its refresh token: the user + the raw token.

    The raw token is carried through so the caller can locate/rotate the stored session
    (which is keyed by the token's hash).
    """

    user: User
    token: str


def _should_verify_csrf(request: Request) -> bool:
    """CSRF is enforced only on cookie-borne tokens for state-changing HTTP methods."""
    return security.config.JWT_COOKIE_CSRF_PROTECT and (request.method.upper() in security.config.JWT_CSRF_METHODS)


class VerifyAuth:
    """Handles authentication via AuthX JWT access token or API key.

    Precedence: an ``X-API-Key`` header wins; otherwise the request is authenticated
    from a JWT access token (read from headers and/or cookies per AuthX config).
    """

    async def get_current_user(
        self,
        request: Request,
        session: AsyncSession = Depends(get_session),
        api_key_value: str | None = Security(api_key_header),
    ) -> User:
        """Get current user using JWT or API Key authentication"""
        if api_key_value is not None:
            return await self._authenticate_with_api_key(session, api_key_value)

        return await self._authenticate_with_jwt(request, session)

    async def get_current_admin_user(
        self,
        request: Request,
        session: AsyncSession = Depends(get_session),
        api_key_value: str | None = Security(api_key_header),
    ) -> User:
        """Get current admin user using JWT or API Key authentication"""
        user = await self.get_current_user(request, session, api_key_value)
        if user.role != "admin":
            raise UnauthorizedException("User is not an admin.")
        return user

    async def get_refresh_auth(
        self,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ) -> RefreshTokenAuth:
        """Authenticate a request by its refresh token (for /refresh and /logout).

        Refresh tokens are only accepted here, never by get_current_user — they are not
        access credentials for the wider API.
        """
        try:
            request_token = await security.get_refresh_token_from_request(request, locations=TOKEN_LOCATIONS)
        except MissingTokenError as e:
            raise UnauthenticatedException("Missing refresh token") from e

        try:
            payload = security.verify_token(request_token, verify_type=True, verify_csrf=_should_verify_csrf(request))
        except AuthXException as e:
            raise UnauthenticatedException("Invalid refresh token") from e

        try:
            user_id = UUID(payload.sub)
        except (TypeError, ValueError) as e:
            raise UnauthenticatedException("Invalid refresh token") from e

        try:
            user = await UserService.for_system(session).get_by_id(user_id)
        except UserNotFoundException as e:
            raise UnauthenticatedException("Invalid refresh token") from e

        return RefreshTokenAuth(user=user, token=request_token.token)

    async def _authenticate_with_jwt(self, request: Request, session: AsyncSession) -> User:
        """Authenticate using a JWT access token verified by AuthX."""
        payload = await self._verify_access_token(request)

        try:
            user_id = UUID(payload.sub)
        except (TypeError, ValueError) as e:
            raise UnauthenticatedException("Invalid token") from e

        try:
            return await UserService.for_system(session).get_by_id(user_id)
        except UserNotFoundException as e:
            raise UnauthenticatedException("User doesn't exist") from e
        except Exception as error:
            log.exception("Unexpected error while authenticating user with JWT: %s", error)
            raise UnauthenticatedException("User doesn't exist") from error

    async def _verify_access_token(self, request: Request):
        """Extract and verify the access token from the request (headers/cookies + CSRF)."""
        # Explicit locations (headers/cookies) so the transport is readable here, even
        # though AuthX would default to the same JWT_TOKEN_LOCATION config.
        try:
            request_token = await security.get_access_token_from_request(request, locations=TOKEN_LOCATIONS)
        except MissingTokenError as e:
            raise UnauthenticatedException("No valid authentication method provided") from e

        try:
            return security.verify_token(request_token, verify_type=True, verify_csrf=_should_verify_csrf(request))
        except AuthXException as e:
            raise UnauthenticatedException("Invalid token") from e

    async def _authenticate_with_api_key(self, session: AsyncSession, api_key_value: str) -> User:
        """Authenticate using API Key - using HMAC-SHA256 for deterministic hashing"""
        try:
            api_key_service = APIKeyService.for_system(session)
            hashed_key = api_key_service.hash_api_key(api_key_value)
            stored_api_key = await api_key_service.get_by_api_key_hash(hashed_key)
            return stored_api_key.user
        except APIKeyNotFoundException as e:
            raise UnauthenticatedException("Invalid API key") from e
        except Exception as error:
            log.exception("Unexpected error while authenticating user with API key: %s", error)
            raise UnauthenticatedException("Invalid API key") from error


# Create instance
auth = VerifyAuth()
