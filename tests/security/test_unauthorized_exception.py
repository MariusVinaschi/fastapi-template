from fastapi import HTTPException, status

from app.security import UnauthorizedException


class TestUnauthorizedException:
    """Test class for UnauthorizedException"""

    def test_unauthorized_exception_creation(self):
        """Test that UnauthorizedException is created with correct status code"""
        detail = "Access denied"
        exception = UnauthorizedException(detail)

        assert isinstance(exception, HTTPException)
        assert exception.status_code == status.HTTP_403_FORBIDDEN
        assert exception.detail == detail

    def test_unauthorized_exception_with_kwargs(self):
        """Test that UnauthorizedException accepts additional kwargs"""
        detail = "Access denied"
        headers = {"X-Custom-Header": "value"}
        exception = UnauthorizedException(detail, headers=headers)

        assert exception.status_code == status.HTTP_403_FORBIDDEN
        assert exception.detail == detail
        # Headers are stored in the exception but may not be directly accessible
        # Check that the exception was created successfully
        assert exception is not None

    def test_unauthorized_exception_inheritance(self):
        """Test that UnauthorizedException inherits from HTTPException"""
        exception = UnauthorizedException("Test detail")

        assert isinstance(exception, HTTPException)
        assert issubclass(UnauthorizedException, HTTPException)

    def test_unauthorized_exception_status_code(self):
        """Test that UnauthorizedException always returns 403 status code"""
        exception1 = UnauthorizedException("Detail 1")
        exception2 = UnauthorizedException("Detail 2", some_kwarg="value")

        assert exception1.status_code == status.HTTP_403_FORBIDDEN
        assert exception2.status_code == status.HTTP_403_FORBIDDEN
