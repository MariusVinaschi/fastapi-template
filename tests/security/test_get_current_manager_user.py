import pytest
from pytest_mock import MockerFixture

from app.security import UnauthorizedException, VerifyTokenJwt
from app.user.factory import UserFactory
from app.user.schemas import RoleEnum


@pytest.mark.asyncio
async def test_get_admin_user(mocker: MockerFixture, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    mocker.patch(
        "app.security.VerifyTokenJwt.get_user_from_token",
        return_value=user,
    )

    result = await VerifyTokenJwt().get_current_manager_user(
        security_scopes=None, session=db_session
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_admin_user_user_not_admin(mocker: MockerFixture, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mocker.patch(
        "app.security.VerifyTokenJwt.get_user_from_token",
        return_value=user,
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        await VerifyTokenJwt().get_current_manager_user(
            security_scopes=None, session=db_session
        )

    assert "User is not a manager." in str(exc_info.value)
