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
    """
    Simulates a race between two concurrent/redelivered `user.created` webhooks
    for the same clerk_id/email pair: by the time `create_user`'s own
    `self._service.create(...)` runs, a conflicting row already exists in the
    DB (inserted "between" the not-found check and the create), so the unique
    constraint on `users.email` raises IntegrityError. The adapter should
    recover by rolling back and returning the already-existing user instead
    of propagating the error.
    """
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

    # First call: the pre-check in create_user - forced to "not found" so the
    # adapter proceeds to self._service.create(...), which then hits the real
    # unique constraint on `email` (existing_user already occupies it).
    # Second call: the adapter's re-fetch-by-clerk_id after catching
    # IntegrityError - left as the real implementation so it performs an
    # actual (post-rollback) DB query and returns a properly bound instance.
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
    """
    Regression test for the gap where `clerk_id` had no DB-level unique
    constraint: a race between two concurrent/redelivered `user.created`
    webhooks for the same `clerk_id` but *different* primary emails (e.g. the
    email changed between event generation and delivery) used to raise no
    `IntegrityError` at all, since only `email` was unique - both inserts
    would silently succeed, producing two rows sharing one `clerk_id`.

    Now that `clerk_id` is also DB-unique (see migration
    28a975b09a5b_add_unique_constraint_on_users_clerk_id), the second insert
    hits the `clerk_id` unique constraint instead, and the adapter recovers
    by re-fetching the winning row and reconciling its email to the payload
    that lost the race.
    """
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
    """
    If `create()` raises IntegrityError but the post-rollback re-fetch by
    clerk_id still finds nothing, the conflict isn't the expected
    same-clerk_id race (e.g. the email belongs to a different, unrelated
    clerk_id) — the adapter must surface a `ValueError` (mapped to 400 by the
    webhook route) instead of the raw `IntegrityError` (which would map to
    500 and cause Clerk to retry a payload that will never succeed).
    """
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
