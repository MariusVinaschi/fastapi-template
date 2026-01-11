import pytest
from pytest_mock import MockerFixture
from fastapi import Request
from fastapi.security import SecurityScopes

from app.api.security import UnauthorizedException, VerifyAuth
from app.domains.users.factory import UserFactory
from app.domains.users.schemas import RoleEnum


@pytest.mark.asyncio
async def test_get_admin_user(mocker: MockerFixture, db_session):
    """Test get_current_admin_user with admin user"""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    mocker.MagicMock(spec=Request)
    mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)

    # Mock get_current_user to return admin user
    mocker.patch.object(VerifyAuth, "get_current_user", return_value=user)

    verify_auth = VerifyAuth()
    result = await verify_auth.get_current_admin_user(
        security_scopes=mock_security_scopes, session=db_session, api_key_value=None, token=None
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_admin_user_user_not_admin(mocker: MockerFixture, db_session):
    """Test get_current_admin_user with non-admin user"""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mocker.MagicMock(spec=Request)
    mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)

    # Mock get_current_user to return standard user
    mocker.patch.object(VerifyAuth, "get_current_user", return_value=user)

    verify_auth = VerifyAuth()
    with pytest.raises(UnauthorizedException) as exc_info:
        await verify_auth.get_current_admin_user(
            security_scopes=mock_security_scopes, session=db_session, api_key_value=None, token=None
        )

    assert "User is not an admin." in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_admin_user_with_jwt_token(mocker: MockerFixture, db_session):
    """Test get_current_admin_user with JWT token"""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    mocker.MagicMock(spec=Request)
    mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)
    mock_token = mocker.MagicMock()

    # Mock get_current_user to return admin user
    mocker.patch.object(VerifyAuth, "get_current_user", return_value=user)

    verify_auth = VerifyAuth()
    result = await verify_auth.get_current_admin_user(
        security_scopes=mock_security_scopes,
        session=db_session,
        api_key_value=None,
        token=mock_token,
    )

    assert result == user
