import pytest

from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.factory import UserFactory
from app.domains.users.service import ClerkUserService


@pytest.mark.anyio
async def test_delete_user(db_session):
    clerk_id = "clerk_id_123"
    await UserFactory.create_async(session=db_session, clerk_id=clerk_id)
    data = {
        "id": clerk_id,
    }
    deleted = await ClerkUserService.for_system(db_session).delete_user(data)
    assert deleted
    with pytest.raises(UserNotFoundException):
        await ClerkUserService.for_system(db_session).get_by_clerk_id(clerk_id)


@pytest.mark.anyio
async def test_delete_user_not_found(db_session):
    clerk_id = "clerk_id_123"
    data = {
        "id": clerk_id,
    }
    with pytest.raises(UserNotFoundException):
        await ClerkUserService.for_system(db_session).delete_user(data)
