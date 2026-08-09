import pytest

from app.domains.users.exceptions import InvalidCredentialsError
from app.domains.users.factory import DEFAULT_TEST_PASSWORD, UserFactory
from app.domains.users.service import UserService


@pytest.mark.anyio
async def test_authenticate_success(db_session):
    user = await UserFactory.create_async(session=db_session, email="user@example.com")

    result = await UserService.for_system(db_session).authenticate("user@example.com", DEFAULT_TEST_PASSWORD)

    assert result.id == user.id


@pytest.mark.anyio
async def test_authenticate_wrong_password_raises(db_session):
    await UserFactory.create_async(session=db_session, email="user@example.com")

    with pytest.raises(InvalidCredentialsError):
        await UserService.for_system(db_session).authenticate("user@example.com", "wrong-password")


@pytest.mark.anyio
async def test_authenticate_unknown_email_raises(db_session):
    with pytest.raises(InvalidCredentialsError):
        await UserService.for_system(db_session).authenticate("nobody@example.com", "whatever12")


@pytest.mark.anyio
async def test_authenticate_empty_password_hash_raises_invalid_not_500(db_session):
    # Rows migrated from Clerk have an empty password_hash; login must fail cleanly (not crash).
    await UserFactory.create_async(session=db_session, email="migrated@example.com", password_hash="")

    with pytest.raises(InvalidCredentialsError):
        await UserService.for_system(db_session).authenticate("migrated@example.com", "any-password")
