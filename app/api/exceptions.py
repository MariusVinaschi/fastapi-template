"""
API exceptions - FastAPI specific HTTP exceptions.
These wrap domain exceptions for HTTP responses.
"""
from fastapi import HTTPException


class NotFoundHTTPException(HTTPException):
    """Base class for all 404 Not Found HTTP exceptions"""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(status_code=404, detail=message)


class UserNotFoundHTTPException(NotFoundHTTPException):
    """HTTP 404 exception for user not found"""

    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message)


class APIKeyNotFoundHTTPException(NotFoundHTTPException):
    """HTTP 404 exception for API key not found"""

    def __init__(self, message: str = "API key not found") -> None:
        super().__init__(message)

