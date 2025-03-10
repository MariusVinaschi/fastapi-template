import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.security import auth
from app.user.factory import UserFactory
from app.user.schemas import RoleEnum
from tests.utils.override_dependencies import DependencyOverrider
from tests.validations.validation_users import (
    valid_dict_content,
    valid_dict_from_value,
)


@pytest.mark.asyncio
async def test_create_user_manager(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    email = "test@test.com"
    first_name = "first_name_admin"
    last_name = "last_name_admin"
    role = "standard"
    with DependencyOverrider(
        app, overrides={auth.get_current_manager_user: lambda: user}
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )
    assert response.status_code == 200
    dict_response = response.json()
    valid_dict_content(dict_response)
    valid_dict_from_value(dict_response, email, first_name, last_name, role)


@pytest.mark.asyncio
async def test_create_user_standard(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    email = "test_basic_user@gmail.com"
    first_name = "first_name_user"
    last_name = "last_name_user"
    role = "standard"
    with DependencyOverrider(
        app, overrides={auth.get_current_manager_user: lambda: user}
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )
    assert response.status_code == 403
    assert response.json() == {"detail": "You are not allowed to create a user"}


@pytest.mark.asyncio
async def test_email_already_exist(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    email = user.email
    first_name = "admin_user_invalid_email"
    last_name = "admin_user_invalid_email"

    with DependencyOverrider(
        app, overrides={auth.get_current_manager_user: lambda: user}
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": "standard",
            },
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "An user with this email already exist"}


# Test: Invalid email
@pytest.mark.asyncio
async def test_invalid_email(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    email = "invalid_email"
    first_name = "invalid_email"
    last_name = "surname_user"
    role = "standard"
    with DependencyOverrider(
        app, overrides={auth.get_current_manager_user: lambda: user}
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )
    assert response.status_code == 422


# Test invalid role
@pytest.mark.asyncio
async def test_invalid_role(client: AsyncClient, app: FastAPI, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    email = "invalid_email"
    first_name = "invalid_email"
    last_name = "surname_user"
    role = "test"
    with DependencyOverrider(
        app, overrides={auth.get_current_manager_user: lambda: user}
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )
    assert response.status_code == 422


# Test: Missing required information
@pytest.mark.asyncio
async def test_missing_required_information(
    client: AsyncClient, app: FastAPI, db_session
):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    first_name = "missing_information"
    last_name = "missing_information"
    with DependencyOverrider(
        app, overrides={auth.get_current_manager_user: lambda: user}
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "role": "standard",
            },
        )
    assert response.status_code == 422
