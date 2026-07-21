import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum
from app.infrastructure.security import auth
from tests.utils.override_dependencies import DependencyOverrider
from tests.validations.validation_users import (
    valid_data_from_user_object,
    valid_dict_content,
)


async def create_test_users(db_session):
    """Helper function to create test users."""
    user_1 = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    user_2 = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    user_3 = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    return [user_1, user_2, user_3]


@pytest.mark.anyio
async def test_retrieve_users_admin(
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


@pytest.mark.anyio
async def test_retrieve_users_with_filters_email(
    app: FastAPI,
    client: AsyncClient,
    db_session,
):
    # Arrange
    users = await create_test_users(db_session)
    target_user = users[1]

    # Act
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: users[0]}):
        response = await client.get(f"/api/v1/users?email={str(target_user.email)}")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["data"][0]["id"] == str(target_user.id)


@pytest.mark.anyio
async def test_retrieve_users_with_filters_role(
    app: FastAPI,
    client: AsyncClient,
    db_session,
):
    # Arrange
    users = await create_test_users(db_session)

    # Act
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: users[0]}):
        response = await client.get("/api/v1/users?role=standard")

    # Assert
    assert response.status_code == 200
    body = response.json()
    standard_users = [u for u in users if u.role == RoleEnum.STANDARD]
    assert body["count"] == len(standard_users)
    returned_ids = {u["id"] for u in body["data"]}
    assert returned_ids == {str(u.id) for u in standard_users}


@pytest.mark.anyio
async def test_retrieve_users_with_filters_clerk_id(
    app: FastAPI,
    client: AsyncClient,
    db_session,
):
    # Arrange
    users = await create_test_users(db_session)
    target_user = users[2]

    # Act
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: users[0]}):
        response = await client.get(f"/api/v1/users?clerk_id={target_user.clerk_id}")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["data"][0]["id"] == str(target_user.id)
