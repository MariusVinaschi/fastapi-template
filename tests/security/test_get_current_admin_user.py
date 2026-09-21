import pytest
from starlette.requests import Request

from app.api.security import UnauthorizedException, auth
from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum
from app.infrastructure.auth import security


def _request(headers: dict[str, str] | None = None, method: str = "GET") -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {"type": "http", "method": method, "path": "/", "headers": raw_headers, "query_string": b""}
    return Request(scope)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_get_current_admin_user_allows_admin(db_session):
    admin = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    token = security.create_access_token(uid=str(admin.id))

    result = await auth.get_current_admin_user(_request(_bearer(token)), db_session, api_key_value=None)

    assert result.id == admin.id


@pytest.mark.anyio
async def test_get_current_admin_user_rejects_standard(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    token = security.create_access_token(uid=str(user.id))

    with pytest.raises(UnauthorizedException):
        await auth.get_current_admin_user(_request(_bearer(token)), db_session, api_key_value=None)
