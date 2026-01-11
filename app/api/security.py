import jwt
from jwt.exceptions import DecodeError, PyJWKClientError
from fastapi import HTTPException, Security, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.config import settings
from app.infrastructure.database import get_session
from app.domains.users.models import User
from app.domains.users.service import APIKeyService, UserService


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403"""
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


class VerifyAuth:
    """Handles both JWT and API Key authentication"""

    def __init__(self):
        self.clerk_issuer = settings.CLERK_FRONTEND_API_URL
        self.clerk_algorithms = settings.CLERK_ALGORITHMS
        self.clerk_azp = settings.CLERK_AZP

        jwks_url = f"{self.clerk_issuer}/.well-known/jwks.json"
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def get_current_user(
        self,
        security_scopes: SecurityScopes,
        session: AsyncSession = Depends(get_session),
        api_key_value: str | None = Security(api_key_header),
        token: HTTPAuthorizationCredentials | None = Security(http_bearer),
    ) -> User:
        """Get current user using JWT or API Key authentication"""
        if api_key_value is not None:
            return await self._authenticate_with_api_key(session, api_key_value)

        # Try JWT authentication first
        if token is not None:
            try:
                return await self._authenticate_with_jwt(security_scopes, session, token)
            except (UnauthenticatedException, UnauthorizedException):
                raise UnauthenticatedException("Invalid token")

        raise UnauthenticatedException("No valid authentication method provided")

    async def get_current_admin_user(
        self,
        security_scopes: SecurityScopes,
        session: AsyncSession = Depends(get_session),
        api_key_value: str | None = Security(api_key_header),
        token: HTTPAuthorizationCredentials | None = Security(http_bearer),
    ) -> User:
        """Get current admin user using JWT or API Key authentication"""
        user = await self.get_current_user(security_scopes, session, api_key_value, token)
        if not user.role == "admin":
            raise UnauthorizedException("User is not an admin.")
        return user

    async def _authenticate_with_jwt(
        self,
        security_scopes: SecurityScopes,
        session: AsyncSession,
        token: HTTPAuthorizationCredentials,
    ) -> User:
        """Authenticate using JWT token"""
        payload = await self._verify_jwt_token(security_scopes, token)
        if "email" not in payload:
            raise UnauthenticatedException("Invalid token")

        try:
            user = await UserService.for_system(session).get_by_email(payload["email"])
        except Exception:
            raise UnauthenticatedException("User doesn't exist")

        return user

    async def _authenticate_with_api_key(
        self,
        session: AsyncSession,
        api_key_value: str,
    ) -> User:
        """Authenticate using API Key - using HMAC-SHA256 for deterministic hashing"""
        try:
            api_key_service = APIKeyService.for_system(session)
            hashed_key = api_key_service.hash_api_key(api_key_value)
            stored_api_key = await api_key_service.get_by_api_key_hash(hashed_key)
            return stored_api_key.user
        except Exception:
            raise UnauthenticatedException("Invalid API key")

    async def _verify_jwt_token(
        self,
        security_scopes: SecurityScopes,
        token: HTTPAuthorizationCredentials,
    ):
        """Verify JWT token using PyJWT"""
        if token is None:
            raise UnauthenticatedException("No token provided")

        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token.credentials).key
        except PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except DecodeError as error:
            raise UnauthorizedException(str(error))
        except Exception:
            raise UnauthorizedException("Check the Clerk frontend API URL and the JWT token")
        try:
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.clerk_algorithms,
                issuer=self.clerk_issuer,
            )
            if payload.get("azp") != self.clerk_azp:
                raise DecodeError("Invalid authorized party")
        except Exception as error:
            raise UnauthorizedException(str(error))

        if len(security_scopes.scopes) > 0:
            self._check_claims(payload, "scope", security_scopes.scopes)

        return payload

    def _check_claims(self, payload, claim_name, expected_value):
        if claim_name not in payload:
            raise UnauthorizedException(detail=f'No claim "{claim_name}" found in token')

        payload_claim = payload[claim_name]

        if claim_name == "scope":
            payload_claim = payload[claim_name].split(" ")

        for value in expected_value:
            if value not in payload_claim:
                raise UnauthorizedException(detail=f'Missing "{claim_name}" scope')


# Create instance
auth = VerifyAuth()
