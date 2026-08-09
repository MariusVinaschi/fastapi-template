import pytest
from httpx import AsyncClient

from app.domains.users.factory import DEFAULT_TEST_PASSWORD, UserFactory


async def _login(client: AsyncClient, email: str) -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD})
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_logout_success(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")
    tokens = await _login(client, "user@example.com")

    response = await client.post("/api/v1/auth/logout", headers=_bearer(tokens["refresh_token"]))

    assert response.status_code == 200


@pytest.mark.anyio
async def test_logout_revokes_refresh_token(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")
    tokens = await _login(client, "user@example.com")

    await client.post("/api/v1/auth/logout", headers=_bearer(tokens["refresh_token"]))

    # The refresh token no longer works after logout.
    response = await client.post("/api/v1/auth/refresh", headers=_bearer(tokens["refresh_token"]))
    assert response.status_code == 401


@pytest.mark.anyio
async def test_logout_without_token_returns_401(client: AsyncClient, db_session):
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 401
