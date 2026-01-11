import pytest

from app.domains.users.factory import UserFactory
from app.domains.users.repository import UserRepository


@pytest.mark.asyncio
async def test_find_by_clerk_id(db_session):
    user = await UserFactory.create_async(session=db_session)
    repository = UserRepository(db_session)
    user = await repository.find_by_clerk_id(user.clerk_id)
    assert user == user


@pytest.mark.asyncio
async def test_find_by_clerk_id_not_found(db_session):
    repository = UserRepository(db_session)
    user = await repository.find_by_clerk_id("nonexistent")
    assert user is None
