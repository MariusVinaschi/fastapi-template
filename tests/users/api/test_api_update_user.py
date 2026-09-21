import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api.security import auth
from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum
from tests.utils.override_dependencies import DependencyOverrider
from tests.validations.validation_users import valid_dict_content


@pytest.mark.anyio
async def test_update_user(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    user_to_update = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(app, overrides={auth.get_current_admin_user: lambda: user}):
        response = await client.patch(
            f"/api/v1/users/{user_to_update.id}",
            json={
                "role": "standard",
            },
        )
    assert response.status_code == 200
    valid_dict_content(response.json())
    assert response.json()["id"] == str(user_to_update.id)
    assert response.json()["email"] == user_to_update.email
    assert response.json()["role"] == "standard"


@pytest.mark.anyio
async def test_invalid_user_id(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    with DependencyOverrider(app, overrides={auth.get_current_admin_user: lambda: user}):
        response = await client.patch(
            "/api/v1/users/cc34ccb8-1b64-11ee-be56-0242ac120002",
            json={
                "role": "standard",
            },
        )
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
