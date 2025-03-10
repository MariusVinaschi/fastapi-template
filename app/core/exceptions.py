from fastapi import HTTPException


class NotFoundHTTPException(HTTPException):
    """Base class for all 404 Not Found exceptions"""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(status_code=404, detail=message)


class CoreException(Exception):
    """Base exception for all domain errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundException(CoreException):
    """Base exception for not found entities"""

    def __init__(self, message: str = "Entity not found"):
        super().__init__(message)


class PermissionDenied(CoreException):
    """Exception for when a user does not have permission to perform an action"""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)
