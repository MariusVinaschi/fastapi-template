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


async def create_test_users(db_session):
    """Helper function to create test users."""
    user_1 = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    user_2 = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    user_3 = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    return [user_1, user_2, user_3]


@pytest.mark.asyncio
async def test_retrieve_users_manager(
    app: FastAPI,
    client: AsyncClient,
    db_session,
):
    # Arrange
    users = await create_test_users(db_session)

    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: users[0]}):
        response = await client.get("/api/v1/users")

    # Assert
    assert response.status_code == 200
    list_users = response.json()["data"]
    assert isinstance(list_users, list)
    assert response.json()["count"] == len(users)

    for user in list_users:
        valid_dict_content(user)
        expected_user = next((u for u in users if user["id"] == str(u.id)), None)
        if expected_user:
            valid_data_from_user_object(user, expected_user)


@pytest.mark.asyncio
async def test_retrieve_users_with_filters_email(
    app: FastAPI,
    client: AsyncClient,
    db_session,
):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.get(f"/api/v1/users?first_name={str(user.first_name)}")
    assert response.status_code == 200
    assert response.json()["count"] == 1
