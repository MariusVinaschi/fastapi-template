import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.exceptions import PermissionDenied
from app.domains.users.authorization import UserAuthorizationAdapter
from app.domains.users.factory import APIKeyFactory, UserFactory
from app.domains.users.schemas import RoleEnum
from app.domains.users.service import APIKeyService


@pytest.mark.anyio
async def test_check_general_permissions_standard_create():
    user = UserFactory.build(role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    assert APIKeyService.for_user(AsyncSession(), context)._check_general_permissions("create") is True


@pytest.mark.anyio
async def test_check_general_permissions_standard_delete():
    user = UserFactory.build(role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    assert APIKeyService.for_user(AsyncSession(), context)._check_general_permissions("delete") is True


@pytest.mark.anyio
async def test_check_general_permissions_standard_read():
    user = UserFactory.build(role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    assert APIKeyService.for_user(AsyncSession(), context)._check_general_permissions("read") is True


@pytest.mark.anyio
async def test_check_general_permissions_standard_list_not_allowed():
    user = UserFactory.build(role=RoleEnum.STANDARD)
    context = UserAuthorizationAdapter(user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        APIKeyService.for_user(AsyncSession(), context)._check_general_permissions("list")


@pytest.mark.anyio
async def test_check_instance_permissions_read_own_key(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    api_key = await APIKeyFactory.create_async(session=db_session, user=user)
    context = UserAuthorizationAdapter(user)
    assert APIKeyService.for_user(db_session, context)._check_instance_permissions("read", api_key) is True


@pytest.mark.anyio
async def test_check_instance_permissions_delete_own_key(db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    api_key = await APIKeyFactory.create_async(session=db_session, user=user)
    context = UserAuthorizationAdapter(user)
    assert APIKeyService.for_user(db_session, context)._check_instance_permissions("delete", api_key) is True


@pytest.mark.anyio
async def test_check_instance_permissions_read_other_users_key_denied(db_session):
    owner = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    other_user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    api_key = await APIKeyFactory.create_async(session=db_session, user=owner)
    context = UserAuthorizationAdapter(other_user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        APIKeyService.for_user(db_session, context)._check_instance_permissions("read", api_key)


@pytest.mark.anyio
async def test_check_instance_permissions_delete_other_users_key_denied(db_session):
    owner = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    other_user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    api_key = await APIKeyFactory.create_async(session=db_session, user=owner)
    context = UserAuthorizationAdapter(other_user)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        APIKeyService.for_user(db_session, context)._check_instance_permissions("delete", api_key)


@pytest.mark.anyio
async def test_check_instance_permissions_admin_cannot_read_other_users_key(db_session):
    """Unlike UserService, APIKeyService grants no admin bypass: API keys are
    strictly self-service, so even an admin must be denied on someone else's key."""
    owner = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    admin = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    api_key = await APIKeyFactory.create_async(session=db_session, user=owner)
    context = UserAuthorizationAdapter(admin)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        APIKeyService.for_user(db_session, context)._check_instance_permissions("read", api_key)


@pytest.mark.anyio
async def test_check_instance_permissions_admin_cannot_delete_other_users_key(db_session):
    """Unlike UserService, APIKeyService grants no admin bypass: API keys are
    strictly self-service, so even an admin must be denied on someone else's key."""
    owner = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    admin = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    api_key = await APIKeyFactory.create_async(session=db_session, user=owner)
    context = UserAuthorizationAdapter(admin)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        APIKeyService.for_user(db_session, context)._check_instance_permissions("delete", api_key)
