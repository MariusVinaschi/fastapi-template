import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.security import auth
from app.user.factory import UserFactory
from app.user.schemas import RoleEnum
from tests.utils.override_dependencies import DependencyOverrider
from tests.validations.validation_users import (
    valid_data_from_user_object,
    valid_dict_content,
)


@pytest.mark.asyncio
async def test_retrieve_manager_user(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.get(f"/api/v1/users/{str(user.id)}")
    assert response.status_code == 200
    valid_dict_content(response.json())
    valid_data_from_user_object(response.json(), user)


@pytest.mark.asyncio
async def test_retrieve_standard_user(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    user_to_retrieve = await UserFactory.create_async(
        session=db_session, role=RoleEnum.STANDARD
    )
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.get(f"/api/v1/users/{str(user_to_retrieve.id)}")

    assert response.status_code == 200
    valid_dict_content(response.json())
    valid_data_from_user_object(response.json(), user_to_retrieve)


@pytest.mark.asyncio
async def test_invalid_user_id(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.get(
            "/api/v1/users/cc34ccb8-1b64-11ee-be56-0242ac120002"
        )
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
