import pytest

from app.user.factory import UserFactory
from app.user.models import UserAuthorizationAdapter


@pytest.mark.asyncio
async def test_user_authorization_adapter(db_session):
    user = await UserFactory.create_async(session=db_session)
    adapter = UserAuthorizationAdapter(user)
    assert adapter.user_id == str(user.id)
    assert adapter.user_email == user.email
    assert adapter.user_role == user.role
