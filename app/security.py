from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import CurrentSession
from app.user.models import User
from app.user.service import UserService


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403"""
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class VerifyTokenJwt:
    """Does all the token verification using PyJWT"""

    def __init__(self):
        self.auth0_api_audience = settings.AUTH0_API_AUDIENCE
        self.auth0_algorithms = settings.AUTH0_ALGORITHMS
        self.auth0_issuer = settings.AUTH0_ISSUER

        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify(
        self,
        security_scopes: SecurityScopes,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer()),
    ):
        if token is None:
            raise UnauthenticatedException

        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                token.credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.auth0_algorithms,
                audience=self.auth0_api_audience,
                issuer=self.auth0_issuer,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))

        if len(security_scopes.scopes) > 0:
            self._check_claims(payload, "scope", security_scopes.scopes)

        return payload

    def _check_claims(self, payload, claim_name, expected_value):
        if claim_name not in payload:
            raise UnauthorizedException(
                detail=f'No claim "{claim_name}" found in token'
            )

        payload_claim = payload[claim_name]

        if claim_name == "scope":
            payload_claim = payload[claim_name].split(" ")

        for value in expected_value:
            if value not in payload_claim:
                raise UnauthorizedException(detail=f'Missing "{claim_name}" scope')

    async def get_user_from_token(
        self,
        security_scopes: SecurityScopes,
        session: AsyncSession,
        token: HTTPAuthorizationCredentials,
    ) -> User:
        payload = await self.verify(security_scopes, token)

        if "email" not in payload:
            raise UnauthenticatedException("Invalid token")

        try:
            user = await UserService(session).get_by_email(payload["email"])
        except Exception:
            raise UnauthenticatedException("User doesn't exist")

        return user

    async def get_current_user(
        self,
        security_scopes: SecurityScopes,
        session: CurrentSession,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer()),
    ) -> User:
        return await self.get_user_from_token(
            security_scopes=security_scopes, token=token, session=session
        )

    async def get_current_manager_user(
        self,
        security_scopes: SecurityScopes,
        session: CurrentSession,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer()),
    ) -> User:
        user = await self.get_user_from_token(
            security_scopes=security_scopes, token=token, session=session
        )
        if not user.role == "manager":
            raise UnauthorizedException("User is not a manager.")

        return user


auth = VerifyTokenJwt()
