import pytest

from app.user.exceptions import UserNotFoundException
from app.user.factory import UserFactory
from app.user.service import UserService


@pytest.mark.asyncio
async def test_find_by_email(db_session):
    user = await UserFactory.create_async(session=db_session)
    service = UserService(db_session)
    user = await service.get_by_email(user.email)
    assert user == user


@pytest.mark.asyncio
async def test_find_by_email_not_found(db_session):
    service = UserService(db_session)
    with pytest.raises(UserNotFoundException):
        await service.get_by_email("nonexistent@example.com")
