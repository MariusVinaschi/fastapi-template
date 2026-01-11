import pytest

from app.domains.base.exceptions import PermissionDenied
from app.domains.users.factory import UserFactory
from app.domains.users.models import UserAuthorizationAdapter
from app.domains.users.schemas import RoleEnum
from app.domains.users.service import UserService


@pytest.mark.asyncio
async def test_check_instance_permissions_admin_read(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    context = UserAuthorizationAdapter(user)
    assert (
        UserService.for_user(db_session, context)._check_instance_permissions("read", user) is True
    )


@pytest.mark.asyncio
async def test_check_instance_permissions_admin_delete(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    context = UserAuthorizationAdapter(user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(db_session, context)._check_instance_permissions("delete", user)


@pytest.mark.asyncio
async def test_check_instance_permissions_admin_update(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    context = UserAuthorizationAdapter(user)
    assert (
        UserService.for_user(db_session, context)._check_instance_permissions("update", user)
        is True
    )


@pytest.mark.asyncio
async def test_check_instance_permissions_standard_update(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    user_to_update = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(db_session, context)._check_instance_permissions(
            "update", user_to_update
        )


@pytest.mark.asyncio
async def test_check_instance_permissions_standard_update_self(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    assert (
        UserService.for_user(db_session, context)._check_instance_permissions("update", user)
        is True
    )


@pytest.mark.asyncio
async def test_check_instance_permissions_standard_read_self(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    assert (
        UserService.for_user(db_session, context)._check_instance_permissions("read", user) is True
    )


@pytest.mark.asyncio
async def test_check_instance_permissions_standard_delete_self(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    user_to_read = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(db_session, context)._check_instance_permissions("read", user_to_read)
