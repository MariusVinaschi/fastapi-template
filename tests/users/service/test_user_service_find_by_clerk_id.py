import pytest

from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.factory import UserFactory
from app.domains.users.models import UserAuthorizationAdapter
from app.domains.users.service import UserService


@pytest.mark.anyio
async def test_find_by_clerk_id(db_session):
    user = await UserFactory.create_async(session=db_session)
    user = await UserService.for_user(db_session, UserAuthorizationAdapter(user)).get_by_clerk_id(
        user.clerk_id
    )
    assert user == user


@pytest.mark.anyio
async def test_find_by_clerk_id_not_found(db_session):
    user = await UserFactory.create_async(session=db_session)
    with pytest.raises(UserNotFoundException):
        await UserService.for_user(db_session, UserAuthorizationAdapter(user)).get_by_clerk_id(
            "nonexistent"
        )
