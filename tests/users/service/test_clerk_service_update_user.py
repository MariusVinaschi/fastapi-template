import pytest

from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.factory import UserFactory
from app.domains.users.service import ClerkUserService


@pytest.mark.asyncio
async def test_update_user(db_session):
    clerk_id = "clerk_id_123"
    await UserFactory.create_async(session=db_session, clerk_id=clerk_id, email="old@example.com")
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": "test@example.com"},
        ],
    }
    updated_user = await ClerkUserService.for_system(db_session).update_user(data)
    assert updated_user.email == "test@example.com"
    assert updated_user.clerk_id == clerk_id


@pytest.mark.asyncio
async def test_update_user_email_already_exists(db_session):
    clerk_id = "clerk_id_123"
    user = await UserFactory.create_async(
        session=db_session, clerk_id=clerk_id, email="old@example.com"
    )
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": user.email},
        ],
    }
    updated_user = await ClerkUserService.for_system(db_session).update_user(data)
    assert updated_user.id == user.id


@pytest.mark.asyncio
async def test_update_user_not_found(db_session):
    clerk_id = "clerk_id_123"
    data = {
        "id": clerk_id,
    }
    with pytest.raises(UserNotFoundException):
        await ClerkUserService.for_system(db_session).update_user(data)
