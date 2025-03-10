import pytest

from app.core.exceptions import PermissionDenied
from app.user.factory import UserFactory
from app.user.models import UserAuthorizationAdapter
from app.user.schemas import RoleEnum
from app.user.service import UserService


@pytest.mark.asyncio
async def test_check_instance_permissions_manager_read(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    service = UserService(session=db_session)

    context = UserAuthorizationAdapter(user)
    assert service._check_instance_permissions("read", context, user) is True


@pytest.mark.asyncio
async def test_check_instance_permissions_manager_delete(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    service = UserService(session=db_session)

    context = UserAuthorizationAdapter(user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        service._check_instance_permissions("delete", context, user)
