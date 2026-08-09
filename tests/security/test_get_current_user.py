from uuid import uuid4

import pytest
from starlette.requests import Request

from app.domains.users.factory import UserFactory
from app.domains.users.service import APIKeyService
from app.infrastructure.auth import security
from app.infrastructure.security import UnauthenticatedException, auth


def _request(headers: dict[str, str] | None = None, method: str = "GET") -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {"type": "http", "method": method, "path": "/", "headers": raw_headers, "query_string": b""}
    return Request(scope)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_get_current_user_with_access_token(db_session):
    user = await UserFactory.create_async(session=db_session)
    token = security.create_access_token(uid=str(user.id))

    result = await auth.get_current_user(_request(_bearer(token)), db_session, api_key_value=None)

    assert result.id == user.id


@pytest.mark.anyio
async def test_get_current_user_with_api_key(db_session):
    user = await UserFactory.create_async(session=db_session)
    generated = await APIKeyService.for_system(db_session).generate_api_key(user)

    result = await auth.get_current_user(_request(), db_session, api_key_value=generated.api_key)

    assert result.id == user.id


@pytest.mark.anyio
async def test_get_current_user_no_credentials_raises(db_session):
    with pytest.raises(UnauthenticatedException):
        await auth.get_current_user(_request(), db_session, api_key_value=None)


@pytest.mark.anyio
async def test_get_current_user_rejects_refresh_token(db_session):
    # A refresh token must not authenticate normal API requests.
    user = await UserFactory.create_async(session=db_session)
    refresh_token = security.create_refresh_token(uid=str(user.id))

    with pytest.raises(UnauthenticatedException):
        await auth.get_current_user(_request(_bearer(refresh_token)), db_session, api_key_value=None)


@pytest.mark.anyio
async def test_get_current_user_rejects_malformed_token(db_session):
    with pytest.raises(UnauthenticatedException):
        await auth.get_current_user(_request(_bearer("not-a-jwt")), db_session, api_key_value=None)


@pytest.mark.anyio
async def test_get_current_user_rejects_unknown_user(db_session):
    token = security.create_access_token(uid=str(uuid4()))

    with pytest.raises(UnauthenticatedException):
        await auth.get_current_user(_request(_bearer(token)), db_session, api_key_value=None)


@pytest.mark.anyio
async def test_get_current_user_rejects_invalid_api_key(db_session):
    with pytest.raises(UnauthenticatedException):
        await auth.get_current_user(_request(), db_session, api_key_value="invalid-key")
