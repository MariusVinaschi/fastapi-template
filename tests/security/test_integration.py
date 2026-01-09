import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes

from app.security import auth, UnauthenticatedException, UnauthorizedException
from app.user.models import User


class TestSecurityIntegration:
    """Integration tests for the complete security system"""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user"""
        user = MagicMock(spec=User)
        user.role = "admin"
        user.email = "admin@test.com"
        return user

    @pytest.fixture
    def mock_standard_user(self):
        """Create mock standard user"""
        user = MagicMock(spec=User)
        user.role = "standard"
        user.email = "user@test.com"
        return user

    @pytest.fixture
    def mock_request_with_api_key(self):
        """Create mock request with API key"""
        request = MagicMock(spec=Request)
        request.headers = {"X-API-Key": "test-api-key"}
        return request

    @pytest.fixture
    def mock_request_without_auth(self):
        """Create mock request without authentication"""
        request = MagicMock(spec=Request)
        request.headers = {}
        return request

    @pytest.fixture
    def mock_jwt_token(self):
        """Create mock JWT token"""
        token = MagicMock(spec=HTTPAuthorizationCredentials)
        token.credentials = "mock.jwt.token"
        return token

    @pytest.fixture
    def mock_security_scopes(self):
        """Create mock security scopes"""
        scopes = MagicMock(spec=SecurityScopes)
        scopes.scopes = []
        return scopes

    @pytest.mark.asyncio
    async def test_complete_jwt_authentication_flow(
        self,
        mock_admin_user,
        mock_jwt_token,
        mock_security_scopes,
        db_session,
        mock_request_without_auth,
    ):
        """Test complete JWT authentication flow"""
        mock_payload = {"email": "admin@test.com", "scope": "read write", "azp": auth.clerk_azp}

        with patch.object(
            auth.jwks_client, "get_signing_key_from_jwt", return_value=MagicMock(key="mock_key")
        ):
            with patch("jwt.decode", return_value=mock_payload):
                with patch("app.security.UserService") as mock_user_service:
                    mock_service_instance = AsyncMock()
                    mock_service_instance.get_by_email.return_value = mock_admin_user
                    mock_user_service.return_value = mock_service_instance

                    result = await auth.get_current_user(
                        security_scopes=mock_security_scopes,
                        session=db_session,
                        api_key_value=None,
                        token=mock_jwt_token,
                    )

                    assert result == mock_admin_user
                    mock_service_instance.get_by_email.assert_called_once_with("admin@test.com")

    @pytest.mark.asyncio
    async def test_complete_api_key_authentication_flow(
        self, mock_standard_user, mock_security_scopes, db_session, mock_request_with_api_key
    ):
        """Test complete API key authentication flow"""
        with patch("app.security.APIKeyService") as mock_api_key_service:
            mock_service_instance = MagicMock()
            mock_service_instance.hash_api_key.return_value = "hashed_key"
            mock_api_key_obj = MagicMock()
            mock_api_key_obj.user = mock_standard_user
            mock_service_instance.get_by_api_key_hash = AsyncMock(return_value=mock_api_key_obj)
            mock_api_key_service.for_system.return_value = mock_service_instance

            result = await auth.get_current_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value="test-api-key",
                token=None,
            )

            assert result == mock_standard_user
            mock_service_instance.hash_api_key.assert_called_once_with("test-api-key")
            mock_service_instance.get_by_api_key_hash.assert_called_once_with("hashed_key")

    @pytest.mark.asyncio
    async def test_jwt_fallback_to_api_key_authentication(
        self, mock_standard_user, mock_security_scopes, db_session, mock_request_with_api_key
    ):
        """Test JWT failure with successful API key fallback"""
        # Test with no JWT token but with API key
        with patch("app.security.APIKeyService") as mock_api_key_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.hash_api_key.return_value = "hashed_key"
            mock_api_key_obj = MagicMock()
            mock_api_key_obj.user = mock_standard_user
            mock_service_instance.get_by_api_key_hash.return_value = mock_api_key_obj
            mock_api_key_service.for_system.return_value = mock_service_instance

            result = await auth.get_current_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value="test-api-key",
                token=None,  # No JWT token
            )

            assert result == mock_standard_user

    @pytest.mark.asyncio
    async def test_admin_authentication_success(
        self,
        mock_admin_user,
        mock_security_scopes,
        db_session,
        mock_request_without_auth,
        mock_jwt_token,
    ):
        """Test successful admin authentication"""
        with patch.object(auth, "get_current_user", return_value=mock_admin_user):
            result = await auth.get_current_admin_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value=None,
                token=mock_jwt_token,
            )

            assert result == mock_admin_user

    @pytest.mark.asyncio
    async def test_admin_authentication_failure_non_admin(
        self,
        mock_standard_user,
        mock_security_scopes,
        db_session,
        mock_request_without_auth,
        mock_jwt_token,
    ):
        """Test admin authentication failure with non-admin user"""
        with patch.object(auth, "get_current_user", return_value=mock_standard_user):
            with pytest.raises(UnauthorizedException) as exc_info:
                await auth.get_current_admin_user(
                    security_scopes=mock_security_scopes,
                    session=db_session,
                    api_key_value=None,
                    token=mock_jwt_token,
                )

            assert "User is not an admin." in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_authentication_methods_provided(
        self, mock_security_scopes, db_session, mock_request_without_auth
    ):
        """Test failure when no authentication methods are provided"""
        with pytest.raises(UnauthenticatedException) as exc_info:
            await auth.get_current_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value=None,
                token=None,
            )

        assert "No valid authentication method provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_jwt_token_verification_with_scopes(
        self, mock_jwt_token, db_session, mock_request_without_auth
    ):
        """Test JWT token verification with security scopes"""
        mock_payload = {
            "email": "admin@test.com",
            "scope": "read write admin",
            "azp": auth.clerk_azp,
        }
        mock_security_scopes = MagicMock(spec=SecurityScopes)
        mock_security_scopes.scopes = ["read", "admin"]

        with patch.object(
            auth.jwks_client, "get_signing_key_from_jwt", return_value=MagicMock(key="mock_key")
        ):
            with patch("jwt.decode", return_value=mock_payload):
                with patch("app.security.UserService") as mock_user_service:
                    mock_service_instance = AsyncMock()
                    mock_service_instance.get_by_email.return_value = MagicMock(role="admin")
                    mock_user_service.return_value = mock_service_instance

                    result = await auth.get_current_user(
                        security_scopes=mock_security_scopes,
                        session=db_session,
                        api_key_value=None,
                        token=mock_jwt_token,
                    )

                    assert result is not None

    @pytest.mark.asyncio
    async def test_jwt_token_verification_missing_scope(
        self, mock_jwt_token, db_session, mock_request_without_auth
    ):
        """Test JWT token verification with missing required scope"""
        mock_payload = {"email": "admin@test.com", "scope": "read write", "azp": auth.clerk_azp}
        mock_security_scopes = MagicMock(spec=SecurityScopes)
        mock_security_scopes.scopes = ["admin"]  # Required scope not in token

        with patch.object(
            auth.jwks_client, "get_signing_key_from_jwt", return_value=MagicMock(key="mock_key")
        ):
            with patch("jwt.decode", return_value=mock_payload):
                with patch("app.security.UserService") as mock_user_service:
                    mock_service_instance = AsyncMock()
                    mock_service_instance.get_by_email.return_value = MagicMock(role="admin")
                    mock_user_service.return_value = mock_service_instance

                    # The UnauthorizedException is caught and converted to UnauthenticatedException
                    with pytest.raises(UnauthenticatedException) as exc_info:
                        await auth.get_current_user(
                            security_scopes=mock_security_scopes,
                            session=db_session,
                            api_key_value=None,
                            token=mock_jwt_token,
                        )

                    assert "Invalid token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_key_authentication_invalid_key(
        self, mock_security_scopes, db_session, mock_request_with_api_key
    ):
        """Test API key authentication with invalid key"""
        with patch("app.security.APIKeyService") as mock_api_key_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.hash_api_key.return_value = "hashed_key"
            mock_service_instance.get_by_api_key_hash.side_effect = Exception("Key not found")
            mock_api_key_service.for_system.return_value = mock_service_instance

            with pytest.raises(UnauthenticatedException) as exc_info:
                await auth.get_current_user(
                    security_scopes=mock_security_scopes,
                    session=db_session,
                    api_key_value="test-api-key",
                    token=None,
                )

            assert "Invalid API key" in str(exc_info.value)
