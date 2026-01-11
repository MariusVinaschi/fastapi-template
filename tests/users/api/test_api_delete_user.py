import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api.security import auth
from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum
from tests.utils.override_dependencies import DependencyOverrider


@pytest.mark.asyncio
async def test_delete_user(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    user_to_delete = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    id = user_to_delete.id
    with DependencyOverrider(app, overrides={auth.get_current_admin_user: lambda: user}):
        response = await client.delete(
            f"/api/v1/users/{id}",
        )
    assert response.status_code == 200
    assert response.json() == {"detail": f"Deleted user {id}"}


@pytest.mark.asyncio
async def test_delete_invalid_id(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    invalid_user_id = "cc34ccb8-1b64-11ee-be56-0242ac120002"
    with DependencyOverrider(app, overrides={auth.get_current_admin_user: lambda: user}):
        response = await client.delete(f"/api/v1/users/{invalid_user_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


@pytest.mark.asyncio
async def test_user_can_delete_himself(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    id = user.id
    with DependencyOverrider(app, overrides={auth.get_current_admin_user: lambda: user}):
        response = await client.delete(
            f"/api/v1/users/{id}",
        )
    assert response.status_code == 403
    assert response.json() == {"detail": "You are not allowed to delete yourself"}
