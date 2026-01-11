import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi.security import SecurityScopes

from app.api.security import auth, VerifyAuth


class TestAuthInstance:
    """Test class for the global auth instance"""

    def test_auth_instance_creation(self):
        """Test that the global auth instance is created correctly"""
        assert isinstance(auth, VerifyAuth)
        assert auth.clerk_issuer is not None
        assert auth.clerk_algorithms is not None
        assert auth.clerk_azp is not None
        assert auth.jwks_client is not None

    @pytest.mark.asyncio
    async def test_auth_get_current_user(self, mocker, db_session):
        """Test get_current_user using the global auth instance"""
        mock_user = MagicMock()
        mocker.MagicMock(spec=Request)
        mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)
        mock_token = mocker.MagicMock()

        # Mock the authentication method
        mocker.patch.object(auth, "_authenticate_with_jwt", return_value=mock_user)

        result = await auth.get_current_user(
            security_scopes=mock_security_scopes,
            session=db_session,
            api_key_value=None,
            token=mock_token,
        )

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_auth_get_current_admin_user(self, mocker, db_session):
        """Test get_current_admin_user using the global auth instance"""
        mock_user = MagicMock()
        mock_user.role = "admin"
        mocker.MagicMock(spec=Request)
        mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)

        # Mock get_current_user to return admin user
        mocker.patch.object(auth, "get_current_user", return_value=mock_user)

        result = await auth.get_current_admin_user(
            security_scopes=mock_security_scopes, session=db_session, api_key_value=None, token=None
        )

        assert result == mock_user

    def test_auth_instance_singleton_behavior(self):
        """Test that the auth instance behaves as a singleton"""
        from app.api.security import auth as auth_imported

        # Both should be the same instance
        assert auth is auth_imported
        assert id(auth) == id(auth_imported)

    @pytest.mark.asyncio
    async def test_auth_check_claims(self):
        """Test check_claims using the global auth instance"""
        payload = {"scope": "read write admin"}
        expected_scopes = ["read", "admin"]

        # Should not raise exception
        auth._check_claims(payload, "scope", expected_scopes)

    @pytest.mark.asyncio
    async def test_auth_verify_jwt_token_mock(self, mocker):
        """Test verify_jwt_token using the global auth instance with mocked dependencies"""
        mock_token = mocker.MagicMock()
        mock_token.credentials = "mock.jwt.token"
        mock_security_scopes = mocker.MagicMock(spec=SecurityScopes)
        mock_security_scopes.scopes = []  # Add scopes attribute
        mock_payload = {"sub": "user123", "scope": "read write", "azp": auth.clerk_azp}

        # Mock the JWKS client and JWT decode
        with patch.object(
            auth.jwks_client, "get_signing_key_from_jwt", return_value=MagicMock(key="mock_key")
        ):
            with patch("jwt.decode", return_value=mock_payload):
                result = await auth._verify_jwt_token(mock_security_scopes, mock_token)

                assert result == mock_payload
