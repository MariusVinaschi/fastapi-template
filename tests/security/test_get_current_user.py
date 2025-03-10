import pytest
from pytest_mock import MockerFixture

from app.security import VerifyTokenJwt
from app.user.factory import UserFactory
from app.user.schemas import RoleEnum


@pytest.mark.asyncio
async def test_get_current_user_manager(mocker: MockerFixture, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.MANAGER)
    mocker.patch(
        "app.security.VerifyTokenJwt.get_user_from_token",
        return_value=user,
    )

    result = await VerifyTokenJwt().get_current_user(
        security_scopes=None, session=db_session
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_current_user_standard(mocker: MockerFixture, db_session):
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mocker.patch(
        "app.security.VerifyTokenJwt.get_user_from_token",
        return_value=user,
    )

    result = await VerifyTokenJwt().get_current_user(
        security_scopes=None, session=db_session
    )

    assert result == user
