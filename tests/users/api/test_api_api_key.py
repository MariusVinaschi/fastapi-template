import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api.rate_limit import limiter
from app.domains.base.exceptions import PermissionDenied
from app.domains.users.service import APIKeyService
from app.infrastructure.security import auth
from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum
from tests.utils.override_dependencies import DependencyOverrider


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The limiter is a process-wide singleton keyed by remote address; reset it so
    these rate-limited endpoints don't leak call counts across test functions."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.mark.anyio
async def test_generate_api_key_for_own_user(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.post("/api/v1/me/api-key")

    assert response.status_code == 200
    assert "api_key" in response.json()


@pytest.mark.anyio
async def test_revoke_api_key_for_own_user(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        generate_response = await client.post("/api/v1/me/api-key")
        assert generate_response.status_code == 200

        response = await client.delete("/api/v1/me/api-key")

    assert response.status_code == 200
    assert response.json() == {"detail": "API key revoked successfully"}


@pytest.mark.anyio
async def test_revoke_api_key_when_none_exists(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.delete("/api/v1/me/api-key")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_generate_api_key_replaces_existing_key(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        first_response = await client.post("/api/v1/me/api-key")
        second_response = await client.post("/api/v1/me/api-key")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["api_key"] != second_response.json()["api_key"]


@pytest.mark.anyio
async def test_generate_api_key_permission_denied_returns_403(app: FastAPI, client: AsyncClient, db_session, mocker):
    """A PermissionDenied raised by the service must surface as 403, not an unhandled 500."""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mocker.patch.object(APIKeyService, "generate_api_key", side_effect=PermissionDenied("Action not allowed"))
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.post("/api/v1/me/api-key")

    assert response.status_code == 403


@pytest.mark.anyio
async def test_revoke_api_key_permission_denied_returns_403(app: FastAPI, client: AsyncClient, db_session, mocker):
    """A PermissionDenied raised by the service must surface as 403, not an unhandled 500."""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mocker.patch.object(APIKeyService, "revoke_api_key", side_effect=PermissionDenied("Action not allowed"))
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.delete("/api/v1/me/api-key")

    assert response.status_code == 403
