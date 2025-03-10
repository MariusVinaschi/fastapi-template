from app.core.exceptions import EntityNotFoundException, NotFoundHTTPException


class UserNotFoundHTTPException(NotFoundHTTPException):
    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message)


class UserNotFoundException(EntityNotFoundException):
    """Domain exception raised when a user is not found in the service layer"""

    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message)
