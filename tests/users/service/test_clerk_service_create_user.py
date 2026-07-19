from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.factory import UserFactory
from app.infrastructure.adapters.clerk import ClerkWebhookAdapter


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
    created_user = await ClerkWebhookAdapter.for_system(db_session).create_user(data)
    assert created_user.clerk_id == clerk_id
    assert created_user.email == "test@example.com"


@pytest.mark.anyio
async def test_create_user_email_already_exists_not_the_same(db_session):
    clerk_id = "clerk_id_123"
    user = await UserFactory.create_async(session=db_session, clerk_id=clerk_id, email="test2@example.com")
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": "test@example.com"},
        ],
    }
    updated_user = await ClerkWebhookAdapter.for_system(db_session).create_user(data)
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
    updated_user = await ClerkWebhookAdapter.for_system(db_session).create_user(data)
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
        await ClerkWebhookAdapter.for_system(db_session).create_user(data)


@pytest.mark.anyio
async def test_create_user_concurrent_duplicate_webhook_is_idempotent(db_session):
    """Race between two `user.created` webhooks for the same clerk_id/email."""
    clerk_id = "clerk_id_123"
    email = "test@example.com"
    existing_user = await UserFactory.create_async(session=db_session, clerk_id=clerk_id, email=email)
    await db_session.commit()
    existing_user_id = existing_user.id

    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": email},
        ],
    }

    adapter = ClerkWebhookAdapter.for_system(db_session)
    real_get_by_clerk_id = adapter._service.get_by_clerk_id

    # 1st call forced to "not found" to reach create(); 2nd call is real, for recovery.
    calls = {"count": 0}

    async def fake_get_by_clerk_id(target_clerk_id: str):
        calls["count"] += 1
        if calls["count"] == 1:
            raise UserNotFoundException
        return await real_get_by_clerk_id(target_clerk_id)

    with (
        patch.object(adapter._service, "get_by_clerk_id", side_effect=fake_get_by_clerk_id),
        patch.object(adapter._service, "get_by_email", side_effect=UserNotFoundException()),
    ):
        result = await adapter.create_user(data)

    assert result.id == existing_user_id
    assert result.clerk_id == clerk_id
    assert result.email == email


@pytest.mark.anyio
async def test_create_user_concurrent_webhook_with_different_email_is_idempotent(db_session):
    """Regression: same clerk_id, different email must still be caught as a race."""
    clerk_id = "clerk_id_123"
    existing_user = await UserFactory.create_async(session=db_session, clerk_id=clerk_id, email="old@example.com")
    await db_session.commit()
    existing_user_id = existing_user.id

    new_email = "new@example.com"
    data = {
        "id": clerk_id,
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": new_email},
        ],
    }

    adapter = ClerkWebhookAdapter.for_system(db_session)
    real_get_by_clerk_id = adapter._service.get_by_clerk_id

    calls = {"count": 0}

    async def fake_get_by_clerk_id(target_clerk_id: str):
        calls["count"] += 1
        if calls["count"] == 1:
            raise UserNotFoundException
        return await real_get_by_clerk_id(target_clerk_id)

    with (
        patch.object(adapter._service, "get_by_clerk_id", side_effect=fake_get_by_clerk_id),
        patch.object(adapter._service, "get_by_email", side_effect=UserNotFoundException()),
    ):
        result = await adapter.create_user(data)

    assert result.id == existing_user_id
    assert result.clerk_id == clerk_id
    assert result.email == new_email


@pytest.mark.anyio
async def test_create_user_raises_value_error_when_conflict_is_not_the_same_clerk_id(db_session):
    """An unrelated conflict must surface as ValueError (400), not a raw IntegrityError."""
    clerk_id = "clerk_id_789"
    email = "unresolvable@example.com"
    data = {
        "id": clerk_id,
        "primary_email_address_id": "1",
        "email_addresses": [{"id": "1", "email_address": email}],
    }

    adapter = ClerkWebhookAdapter.for_system(db_session)
    original_error = IntegrityError("INSERT INTO users ...", {}, Exception("unique violation"))

    async def fake_create(_data):
        raise original_error

    with (
        patch.object(adapter._service, "get_by_clerk_id", side_effect=UserNotFoundException()),
        patch.object(adapter._service, "get_by_email", side_effect=UserNotFoundException()),
        patch.object(adapter._service, "create", side_effect=fake_create),
    ):
        with pytest.raises(ValueError) as exc_info:
            await adapter.create_user(data)

    assert exc_info.value.__cause__ is original_error
