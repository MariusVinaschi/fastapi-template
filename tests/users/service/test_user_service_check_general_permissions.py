from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.authorization import AuthorizationContext
from app.domains.base.exceptions import PermissionDenied
from app.domains.users.schemas import RoleEnum
from app.domains.users.service import UserService


class MockAuthorizationContext(AuthorizationContext):
    def __init__(self, user_role: RoleEnum, user_id: str | None = None, user_email: str = "test@example.com"):
        self._user_id = user_id or str(uuid4())
        self._user_email = user_email
        self._user_role = str(user_role)

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def user_email(self) -> str:
        return self._user_email

    @property
    def user_role(self) -> str:
        return self._user_role


@pytest.mark.anyio
async def test_check_general_permissions_admin_create():
    context = MockAuthorizationContext(user_role="admin")
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("create") is True


@pytest.mark.anyio
async def test_check_general_permissions_admin_read():
    context = MockAuthorizationContext(user_role="admin")
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("read") is True


@pytest.mark.anyio
async def test_check_general_permissions_admin_list():
    context = MockAuthorizationContext(user_role="admin")
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("list") is True


@pytest.mark.anyio
async def test_check_general_permissions_admin_delete():
    context = MockAuthorizationContext(user_role="admin")
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("delete") is True


@pytest.mark.anyio
async def test_check_general_permissions_standard_create():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(AsyncSession(), context)._check_general_permissions("create")


@pytest.mark.anyio
async def test_check_general_permissions_standard_update():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("update") is True


@pytest.mark.anyio
async def test_check_general_permissions_standard_read():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    assert UserService.for_user(AsyncSession(), context)._check_general_permissions("read") is True


@pytest.mark.anyio
async def test_check_general_permissions_standard_list():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(AsyncSession(), context)._check_general_permissions("list")


@pytest.mark.anyio
async def test_check_general_permissions_standard_delete():
    context = MockAuthorizationContext(user_role=RoleEnum.STANDARD)
    with pytest.raises(PermissionDenied, match="Action not allowed"):
        UserService.for_user(AsyncSession(), context)._check_general_permissions("delete")
