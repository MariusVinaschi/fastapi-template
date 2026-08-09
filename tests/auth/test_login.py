import pytest
from httpx import AsyncClient

from app.domains.users.factory import DEFAULT_TEST_PASSWORD, UserFactory


@pytest.mark.anyio
async def test_login_success_returns_tokens(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")

    response = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": DEFAULT_TEST_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password_returns_401(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")

    response = await client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong-password"})

    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_unknown_email_returns_401(client: AsyncClient, db_session):
    response = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever12"})

    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_response_has_no_password_hash(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")

    response = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": DEFAULT_TEST_PASSWORD}
    )

    assert "password_hash" not in response.text
