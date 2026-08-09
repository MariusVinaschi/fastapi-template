import pytest
from httpx import AsyncClient

from app.domains.users.factory import DEFAULT_TEST_PASSWORD, UserFactory


async def _login(client: AsyncClient, email: str) -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD})
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_refresh_returns_new_pair(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")
    tokens = await _login(client, "user@example.com")

    response = await client.post("/api/v1/auth/refresh", headers=_bearer(tokens["refresh_token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["refresh_token"] != tokens["refresh_token"]


@pytest.mark.anyio
async def test_refresh_reuse_is_detected_and_revokes_family(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")
    tokens = await _login(client, "user@example.com")

    rotated = await client.post("/api/v1/auth/refresh", headers=_bearer(tokens["refresh_token"]))
    new_refresh = rotated.json()["refresh_token"]

    # Replaying the consumed refresh token is rejected...
    replay = await client.post("/api/v1/auth/refresh", headers=_bearer(tokens["refresh_token"]))
    assert replay.status_code == 401

    # ...and the whole family is revoked, so the live successor is dead too.
    after = await client.post("/api/v1/auth/refresh", headers=_bearer(new_refresh))
    assert after.status_code == 401


@pytest.mark.anyio
async def test_refresh_without_token_returns_401(client: AsyncClient, db_session):
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_refresh_rejects_access_token(client: AsyncClient, db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")
    tokens = await _login(client, "user@example.com")

    response = await client.post("/api/v1/auth/refresh", headers=_bearer(tokens["access_token"]))

    assert response.status_code == 401
