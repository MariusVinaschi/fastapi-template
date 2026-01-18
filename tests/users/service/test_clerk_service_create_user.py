import pytest

from app.domains.users.factory import UserFactory
from app.domains.users.service import ClerkUserService


@pytest.mark.anyio
async def test_create_user(db_session):
    clerk_id = "clerk_id_123"
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": "test@example.com"},
        ],
    }
    created_user = await ClerkUserService.for_system(db_session).create_user(data)
    assert created_user.clerk_id == clerk_id
    assert created_user.email == "test@example.com"


@pytest.mark.anyio
async def test_create_user_email_already_exists_not_the_same(db_session):
    clerk_id = "clerk_id_123"
    user = await UserFactory.create_async(
        session=db_session, clerk_id=clerk_id, email="test2@example.com"
    )
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": "test@example.com"},
        ],
    }
    updated_user = await ClerkUserService.for_system(db_session).create_user(data)
    assert updated_user.clerk_id == clerk_id
    assert updated_user.email == "test@example.com"
    assert updated_user.id == user.id


@pytest.mark.anyio
async def test_create_user_email_already_exists_the_same(db_session):
    clerk_id = "clerk_id_123"
    email = "test@example.com"
    user = await UserFactory.create_async(session=db_session, clerk_id=clerk_id, email=email)
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": email},
        ],
    }
    updated_user = await ClerkUserService.for_system(db_session).create_user(data)
    assert updated_user.clerk_id == clerk_id
    assert updated_user.email == email
    assert updated_user.id == user.id


@pytest.mark.anyio
async def test_create_user_clerk_id_not_found_but_email_exists(db_session):
    clerk_id = "clerk_id_123"
    email = "test@example.com"
    await UserFactory.create_async(session=db_session, email=email)
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": email},
        ],
    }
    with pytest.raises(ValueError):
        await ClerkUserService.for_system(db_session).create_user(data)
