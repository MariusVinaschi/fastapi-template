import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDenied
from app.user.schemas import RoleEnum
from app.user.service import UserService


class MockAuthorizationContext:
    def __init__(self, user_role: RoleEnum):
        self.user_role = user_role


@pytest.mark.asyncio
async def test_check_general_permissions_manager_create():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.MANAGER)
    assert service._check_general_permissions("create", context) is True


@pytest.mark.asyncio
async def test_check_general_permissions_manager_read():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.MANAGER)
    assert service._check_general_permissions("read", context) is True


@pytest.mark.asyncio
async def test_check_general_permissions_manager_list():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.MANAGER)
    assert service._check_general_permissions("list", context) is True


@pytest.mark.asyncio
async def test_check_general_permissions_manager_delete():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.MANAGER)
    assert service._check_general_permissions("delete", context) is True


@pytest.mark.asyncio
async def test_check_general_permissions_standard_create():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        service._check_general_permissions("create", context)


@pytest.mark.asyncio
async def test_check_general_permissions_standard_update():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        service._check_general_permissions("update", context)


@pytest.mark.asyncio
async def test_check_general_permissions_standard_read():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    assert service._check_general_permissions("read", context) is True


@pytest.mark.asyncio
async def test_check_general_permissions_standard_list():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    assert service._check_general_permissions("list", context) is True


@pytest.mark.asyncio
async def test_check_general_permissions_standard_delete():
    service = UserService(session=AsyncSession())
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        service._check_general_permissions("delete", context)
