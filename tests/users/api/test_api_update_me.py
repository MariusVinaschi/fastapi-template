import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api.security import auth
from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum
from tests.utils.override_dependencies import DependencyOverrider
from tests.validations.validation_users import valid_dict_content


@pytest.mark.asyncio
async def test_update_me(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(app, overrides={auth.get_current_user: lambda: user}):
        response = await client.patch(
            "/api/v1/me",
            json={
                "configuration": {
                    "widgets": [
                        {"id": 1, "x": 0, "y": 0},
                        {"id": 2, "x": 1, "y": 1},
                        {"id": 3, "x": 2, "y": 2},
                    ],
                },
            },
        )
    assert response.status_code == 200
    valid_dict_content(response.json())
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == user.email
    assert response.json()["role"] == user.role
    assert response.json()["configuration"] == {
        "widgets": [
            {"id": 1, "x": 0, "y": 0},
            {"id": 2, "x": 1, "y": 1},
            {"id": 3, "x": 2, "y": 2},
        ]
    }


@pytest.mark.asyncio
async def test_update_me_invalid_role(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    with DependencyOverrider(
        app,
        overrides={auth.get_current_user: lambda: user},
    ):
        response = await client.patch("/api/v1/me", json={"role": "admin"})
    assert response.status_code == 200
    valid_dict_content(response.json())
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == user.email
    assert response.json()["role"] == user.role
    assert response.json()["configuration"] == user.configuration


@pytest.mark.asyncio
async def test_update_me_invalid_configuration(app: FastAPI, client: AsyncClient, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    with DependencyOverrider(
        app,
        overrides={auth.get_current_user: lambda: user},
    ):
        response = await client.patch(
            "/api/v1/me", json={"configuration": [{"id": 1, "x": 0, "y": 0}]}
        )
    assert response.status_code == 422
