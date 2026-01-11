import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.exceptions import PermissionDenied
from app.domains.users.schemas import RoleEnum
from app.domains.users.service import UserService


class MockAuthorizationContext:
    def __init__(self, user_role: RoleEnum):
        self.user_role = user_role


@pytest.mark.asyncio
async def test_check_general_permissions_admin_create():
    context = MockAuthorizationContext(user_role=RoleEnum.ADMIN)
    assert (
        UserService.for_user(AsyncSession(), context)._check_general_permissions("create") is True
    )


@pytest.mark.asyncio
async def test_check_general_permissions_admin_read():
    context = MockAuthorizationContext(user_role=RoleEnum.ADMIN)
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("read") is True


@pytest.mark.asyncio
async def test_check_general_permissions_admin_list():
    context = MockAuthorizationContext(user_role=RoleEnum.ADMIN)
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("list") is True


@pytest.mark.asyncio
async def test_check_general_permissions_admin_delete():
    context = MockAuthorizationContext(user_role=RoleEnum.ADMIN)
    assert (
        UserService.for_user(AsyncSession(), context)._check_general_permissions("delete") is True
    )


@pytest.mark.asyncio
async def test_check_general_permissions_standard_create():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(AsyncSession(), context)._check_general_permissions("create")


@pytest.mark.asyncio
async def test_check_general_permissions_standard_update():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    assert (
        UserService.for_user(AsyncSession(), context)._check_general_permissions("update") is True
    )


@pytest.mark.asyncio
async def test_check_general_permissions_standard_read():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("read") is True


@pytest.mark.asyncio
async def test_check_general_permissions_standard_list():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(AsyncSession(), context)._check_general_permissions("list")


@pytest.mark.asyncio
async def test_check_general_permissions_standard_delete():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(AsyncSession(), context)._check_general_permissions("delete")
