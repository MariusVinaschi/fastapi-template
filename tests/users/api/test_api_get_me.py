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
async def test_get_me_user_manager(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    with DependencyOverrider(
        app,
        overrides={auth.get_current_user: lambda: user},
    ):
        response = await client.get("/api/v1/me")
        assert response.status_code == 200
        valid_dict_content(response.json())
        valid_data_from_user_object(response.json(), user)


@pytest.mark.asyncio
async def test_get_me_user_standard(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(
        app,
        overrides={auth.get_current_user: lambda: user},
    ):
        response = await client.get("/api/v1/me")
        assert response.status_code == 200
        valid_dict_content(response.json())
        valid_data_from_user_object(response.json(), user)
