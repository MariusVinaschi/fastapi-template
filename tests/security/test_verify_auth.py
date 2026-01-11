import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes

from app.api.security import VerifyAuth, UnauthenticatedException, UnauthorizedException
from app.domains.users.models import User


class TestVerifyAuth:
    """Test class for VerifyAuth"""

    @pytest.fixture
    def verify_auth(self):
        """Create VerifyAuth instance for testing"""
        return VerifyAuth()

    @pytest.fixture
    def mock_user_admin(self):
        """Create mock admin user"""
        user = MagicMock(spec=User)
        user.role = "admin"
        user.email = "admin@test.com"
        return user

    @pytest.fixture
    def mock_user_standard(self):
        """Create mock standard user"""
        user = MagicMock(spec=User)
        user.role = "standard"
        user.email = "user@test.com"
        return user

    @pytest.fixture
    def mock_token(self):
        """Create mock JWT token"""
        token = MagicMock(spec=HTTPAuthorizationCredentials)
        token.credentials = "mock.jwt.token"
        return token

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = MagicMock(spec=Request)
        request.headers = {}
        return request

    @pytest.fixture
    def mock_security_scopes(self):
        """Create mock security scopes"""
        scopes = MagicMock(spec=SecurityScopes)
        scopes.scopes = []
        return scopes

    def test_verify_auth_initialization(self, verify_auth):
        """Test VerifyAuth initialization"""
        assert verify_auth.clerk_issuer is not None
        assert verify_auth.clerk_algorithms is not None
        assert verify_auth.clerk_azp is not None
        assert verify_auth.jwks_client is not None

    @pytest.mark.asyncio
    async def test_get_current_user_with_jwt_success(
        self,
        verify_auth,
        mock_user_admin,
        mock_token,
        mock_security_scopes,
        db_session,
        mock_request,
    ):
        """Test successful JWT authentication"""
        with patch.object(
            verify_auth, "_authenticate_with_jwt", return_value=mock_user_admin
        ) as mock_jwt:
            result = await verify_auth.get_current_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value=None,
                token=mock_token,
            )

            assert result == mock_user_admin
            mock_jwt.assert_called_once_with(mock_security_scopes, db_session, mock_token)

    @pytest.mark.asyncio
    async def test_get_current_user_with_jwt_failure_then_api_key_success(
        self, verify_auth, mock_user_admin, mock_security_scopes, db_session, mock_request
    ):
        """Test JWT failure followed by successful API key authentication"""
        # Test with no token (JWT) but with API key
        with patch.object(
            verify_auth, "_authenticate_with_api_key", return_value=mock_user_admin
        ) as mock_api:
            result = await verify_auth.get_current_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value="test-api-key",
                token=None,  # No JWT token
            )

            assert result == mock_user_admin
            mock_api.assert_called_once_with(db_session, "test-api-key")

    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(
        self,
        verify_auth,
        mock_user_admin,
        mock_security_scopes,
        db_session,
        mock_request,
        mock_token,
    ):
        """Test successful admin user authentication"""
        with patch.object(verify_auth, "get_current_user", return_value=mock_user_admin):
            result = await verify_auth.get_current_admin_user(
                security_scopes=mock_security_scopes,
                session=db_session,
                api_key_value=None,
                token=mock_token,
            )

            assert result == mock_user_admin

    @pytest.mark.asyncio
    async def test_get_current_admin_user_not_admin(
        self,
        verify_auth,
        mock_user_standard,
        mock_security_scopes,
        db_session,
        mock_request,
        mock_token,
    ):
        """Test failure when user is not admin"""
        with patch.object(verify_auth, "get_current_user", return_value=mock_user_standard):
            with pytest.raises(UnauthorizedException) as exc_info:
                await verify_auth.get_current_admin_user(
                    security_scopes=mock_security_scopes,
                    session=db_session,
                    api_key_value=None,
                    token=mock_token,
                )

            assert "User is not an admin." in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_with_jwt_success(
        self, verify_auth, mock_user_admin, mock_token, mock_security_scopes, db_session
    ):
        """Test successful JWT authentication"""
        mock_payload = {"email": "admin@test.com"}

        with patch.object(verify_auth, "_verify_jwt_token", return_value=mock_payload):
            with patch("app.security.UserService") as mock_user_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_by_email.return_value = mock_user_admin
                mock_user_service.return_value = mock_service_instance

                result = await verify_auth._authenticate_with_jwt(
                    mock_security_scopes, db_session, mock_token
                )

                assert result == mock_user_admin
                mock_service_instance.get_by_email.assert_called_once_with("admin@test.com")

    @pytest.mark.asyncio
    async def test_authenticate_with_jwt_invalid_token(
        self, verify_auth, mock_token, mock_security_scopes, db_session
    ):
        """Test JWT authentication with invalid token"""
        mock_payload = {"sub": "user123"}  # Missing email

        with patch.object(verify_auth, "_verify_jwt_token", return_value=mock_payload):
            with pytest.raises(UnauthenticatedException) as exc_info:
                await verify_auth._authenticate_with_jwt(
                    mock_security_scopes, db_session, mock_token
                )

            assert "Invalid token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_with_jwt_user_not_found(
        self, verify_auth, mock_token, mock_security_scopes, db_session
    ):
        """Test JWT authentication when user doesn't exist"""
        mock_payload = {"email": "nonexistent@test.com"}

        with patch.object(verify_auth, "_verify_jwt_token", return_value=mock_payload):
            with patch("app.security.UserService") as mock_user_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_by_email.side_effect = Exception("User not found")
                mock_user_service.return_value = mock_service_instance

                with pytest.raises(UnauthenticatedException) as exc_info:
                    await verify_auth._authenticate_with_jwt(
                        mock_security_scopes, db_session, mock_token
                    )

                assert "User doesn't exist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key_success(
        self, verify_auth, mock_user_admin, db_session
    ):
        """Test successful API key authentication"""
        with patch("app.security.APIKeyService") as mock_api_key_service:
            mock_service_instance = MagicMock()
            mock_service_instance.hash_api_key.return_value = "hashed_key"
            mock_api_key_obj = MagicMock()
            mock_api_key_obj.user = mock_user_admin
            mock_service_instance.get_by_api_key_hash = AsyncMock(return_value=mock_api_key_obj)
            mock_api_key_service.for_system.return_value = mock_service_instance

            result = await verify_auth._authenticate_with_api_key(db_session, "test-api-key")

            assert result == mock_user_admin
            mock_service_instance.hash_api_key.assert_called_once_with("test-api-key")
            mock_service_instance.get_by_api_key_hash.assert_called_once_with("hashed_key")

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key_invalid(self, verify_auth, db_session):
        """Test API key authentication with invalid key"""
        with patch("app.security.APIKeyService") as mock_api_key_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.hash_api_key.return_value = "hashed_key"
            mock_service_instance.get_by_api_key_hash.side_effect = Exception("Key not found")
            mock_api_key_service.for_system.return_value = mock_service_instance

            with pytest.raises(UnauthenticatedException) as exc_info:
                await verify_auth._authenticate_with_api_key(db_session, "invalid-key")

            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_jwt_token_success(self, verify_auth, mock_token, mock_security_scopes):
        """Test successful JWT token verification"""
        mock_payload = {"sub": "user123", "scope": "read write", "azp": verify_auth.clerk_azp}
        mock_signing_key = "mock_signing_key"

        with patch.object(
            verify_auth.jwks_client,
            "get_signing_key_from_jwt",
            return_value=MagicMock(key=mock_signing_key),
        ):
            with patch("jwt.decode", return_value=mock_payload) as mock_decode:
                result = await verify_auth._verify_jwt_token(mock_security_scopes, mock_token)

                assert result == mock_payload
                mock_decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_jwt_token_no_token(self, verify_auth, mock_security_scopes):
        """Test JWT verification with no token"""
        with pytest.raises(UnauthenticatedException) as exc_info:
            await verify_auth._verify_jwt_token(mock_security_scopes, None)

        assert "No token provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_jwt_token_jwks_error(self, verify_auth, mock_token, mock_security_scopes):
        """Test JWT verification with JWKS client error"""
        import jwt.exceptions

        with patch.object(
            verify_auth.jwks_client,
            "get_signing_key_from_jwt",
            side_effect=jwt.exceptions.PyJWKClientError("JWKS error"),
        ):
            with pytest.raises(UnauthorizedException) as exc_info:
                await verify_auth._verify_jwt_token(mock_security_scopes, mock_token)

            assert "JWKS error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_jwt_token_decode_error(
        self, verify_auth, mock_token, mock_security_scopes
    ):
        """Test JWT verification with decode error"""
        mock_signing_key = "mock_signing_key"

        with patch.object(
            verify_auth.jwks_client,
            "get_signing_key_from_jwt",
            return_value=MagicMock(key=mock_signing_key),
        ):
            with patch("jwt.decode", side_effect=Exception("Decode error")):
                with pytest.raises(UnauthorizedException) as exc_info:
                    await verify_auth._verify_jwt_token(mock_security_scopes, mock_token)

                assert "Decode error" in str(exc_info.value)

    def test_check_claims_success(self, verify_auth):
        """Test successful claims checking"""
        payload = {"scope": "read write admin"}
        expected_scopes = ["read", "admin"]

        # Should not raise exception
        verify_auth._check_claims(payload, "scope", expected_scopes)

    def test_check_claims_missing_claim(self, verify_auth):
        """Test claims checking with missing claim"""
        payload = {"sub": "user123"}
        expected_scopes = ["read"]

        with pytest.raises(UnauthorizedException) as exc_info:
            verify_auth._check_claims(payload, "scope", expected_scopes)

        assert 'No claim "scope" found in token' in str(exc_info.value)

    def test_check_claims_missing_scope(self, verify_auth):
        """Test claims checking with missing scope"""
        payload = {"scope": "read write"}
        expected_scopes = ["admin"]

        with pytest.raises(UnauthorizedException) as exc_info:
            verify_auth._check_claims(payload, "scope", expected_scopes)

        assert 'Missing "scope" scope' in str(exc_info.value)

    def test_check_claims_non_scope_claim(self, verify_auth):
        """Test claims checking with non-scope claim"""
        payload = {"role": "admin"}
        expected_roles = ["admin"]

        # Should not raise exception
        verify_auth._check_claims(payload, "role", expected_roles)
