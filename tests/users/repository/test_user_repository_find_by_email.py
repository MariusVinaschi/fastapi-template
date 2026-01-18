import pytest

from app.domains.users.factory import UserFactory
from app.domains.users.repository import UserRepository


@pytest.mark.anyio
async def test_find_by_email(db_session):
    user = await UserFactory.create_async(session=db_session)
    repository = UserRepository(db_session)
    user = await repository.find_by_email(user.email)
    assert user == user


@pytest.mark.anyio
async def test_find_by_email_not_found(db_session):
    repository = UserRepository(db_session)
    user = await repository.find_by_email("nonexistent@example.com")
    assert user is None
