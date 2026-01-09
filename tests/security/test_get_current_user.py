import pytest
from pytest_mock import MockerFixture
from fastapi import Request
from fastapi.security import SecurityScopes

from app.security import VerifyAuth
from app.user.factory import UserFactory
from app.user.schemas import RoleEnum


@pytest.mark.asyncio
async def test_get_current_user_admin(mocker: MockerFixture, db_session):
    """Test get_current_user with admin user"""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    mock_request = mocker.MagicMock(spec=Request)
    mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)
    mock_token = mocker.MagicMock()

    # Mock the authentication methods to return the user
    mocker.patch.object(VerifyAuth, "_authenticate_with_jwt", return_value=user)

    verify_auth = VerifyAuth()
    result = await verify_auth.get_current_user(
        security_scopes=mock_security_scopes,
        session=db_session,
        api_key_value=None,
        token=mock_token,
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_current_user_standard(mocker: MockerFixture, db_session):
    """Test get_current_user with standard user"""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mock_request = mocker.MagicMock(spec=Request)
    mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)
    mock_token = mocker.MagicMock()

    # Mock the authentication methods to return the user
    mocker.patch.object(VerifyAuth, "_authenticate_with_jwt", return_value=user)

    verify_auth = VerifyAuth()
    result = await verify_auth.get_current_user(
        security_scopes=mock_security_scopes,
        session=db_session,
        api_key_value=None,
        token=mock_token,
    )

    assert result == user


@pytest.mark.asyncio
async def test_get_current_user_with_api_key(mocker: MockerFixture, db_session):
    """Test get_current_user with API key authentication"""
    user = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    mock_request = mocker.MagicMock(spec=Request)
    mock_request.headers = {"X-API-Key": "test-api-key"}
    mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)

    # Mock API key success (no JWT token)
    mocker.patch.object(VerifyAuth, "_authenticate_with_api_key", return_value=user)

    verify_auth = VerifyAuth()
    result = await verify_auth.get_current_user(
        security_scopes=mock_security_scopes,
        session=db_session,
        api_key_value="test-api-key",
        token=None,  # No JWT token
    )

    assert result == user
