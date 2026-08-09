from uuid import uuid4

import pytest
from starlette.requests import Request

from app.domains.users.factory import UserFactory
from app.infrastructure.auth import security
from app.infrastructure.security import RefreshTokenAuth, UnauthenticatedException, auth


def _request(headers: dict[str, str] | None = None, method: str = "POST") -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": method,
        "path": "/",
        "headers": raw_headers,
        "query_string": b"",
    }
    return Request(scope)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_get_refresh_auth_returns_user_and_raw_token(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    token = security.create_refresh_token(uid=str(user.id))
    request = _request(_bearer(token))

    # Act
    result = await auth.get_refresh_auth(request, db_session)

    # Assert
    assert isinstance(result, RefreshTokenAuth)
    assert result.user.id == user.id
    assert result.token == token


@pytest.mark.anyio
async def test_get_refresh_auth_missing_token_raises(db_session):
    # Arrange
    request = _request()

    # Act / Assert
    with pytest.raises(UnauthenticatedException):
        await auth.get_refresh_auth(request, db_session)


@pytest.mark.anyio
async def test_get_refresh_auth_rejects_access_token(db_session):
    # Arrange - an access token must not be accepted where a refresh token is required
    user = await UserFactory.create_async(session=db_session)
    access_token = security.create_access_token(uid=str(user.id))
    request = _request(_bearer(access_token))

    # Act / Assert
    with pytest.raises(UnauthenticatedException):
        await auth.get_refresh_auth(request, db_session)


@pytest.mark.anyio
async def test_get_refresh_auth_rejects_malformed_token(db_session):
    # Arrange
    request = _request(_bearer("not-a-valid-jwt"))

    # Act / Assert
    with pytest.raises(UnauthenticatedException):
        await auth.get_refresh_auth(request, db_session)


@pytest.mark.anyio
async def test_get_refresh_auth_rejects_unknown_user(db_session):
    # Arrange - validly signed refresh token whose subject has no user row
    token = security.create_refresh_token(uid=str(uuid4()))
    request = _request(_bearer(token))

    # Act / Assert
    with pytest.raises(UnauthenticatedException):
        await auth.get_refresh_auth(request, db_session)
