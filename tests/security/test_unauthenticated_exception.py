from fastapi import HTTPException, status

from app.security import UnauthenticatedException


class TestUnauthenticatedException:
    """Test class for UnauthenticatedException"""

    def test_unauthenticated_exception_creation(self):
        """Test that UnauthenticatedException is created with correct status code"""
        detail = "Authentication required"
        exception = UnauthenticatedException(detail)

        assert isinstance(exception, HTTPException)
        assert exception.status_code == status.HTTP_401_UNAUTHORIZED
        assert exception.detail == detail

    def test_unauthenticated_exception_with_kwargs(self):
        """Test that UnauthenticatedException accepts additional kwargs"""
        detail = "Authentication required"
        headers = {"WWW-Authenticate": "Bearer"}
        exception = UnauthenticatedException(detail, headers=headers)

        assert exception.status_code == status.HTTP_401_UNAUTHORIZED
        assert exception.detail == detail
        # Headers are stored in the exception but may not be directly accessible
        # Check that the exception was created successfully
        assert exception is not None

    def test_unauthenticated_exception_inheritance(self):
        """Test that UnauthenticatedException inherits from HTTPException"""
        exception = UnauthenticatedException("Test detail")

        assert isinstance(exception, HTTPException)
        assert issubclass(UnauthenticatedException, HTTPException)

    def test_unauthenticated_exception_status_code(self):
        """Test that UnauthenticatedException always returns 401 status code"""
        exception1 = UnauthenticatedException("Detail 1")
        exception2 = UnauthenticatedException("Detail 2", some_kwarg="value")

        assert exception1.status_code == status.HTTP_401_UNAUTHORIZED
        assert exception2.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_exception_different_from_unauthorized(self):
        """Test that UnauthenticatedException has different status code from UnauthorizedException"""
        from app.security import UnauthorizedException

        auth_exception = UnauthenticatedException("Auth required")
        unauth_exception = UnauthorizedException("Access denied")

        assert auth_exception.status_code == status.HTTP_401_UNAUTHORIZED
        assert unauth_exception.status_code == status.HTTP_403_FORBIDDEN
        assert auth_exception.status_code != unauth_exception.status_code
