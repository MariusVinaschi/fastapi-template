"""
User domain exceptions - Framework agnostic.
These exceptions are raised by user services and should be
caught and transformed by the delivery layer.
"""
from app.domains.base.exceptions import EntityNotFoundException


class UserNotFoundException(EntityNotFoundException):
    """Domain exception raised when a user is not found"""

    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message)


class APIKeyNotFoundException(EntityNotFoundException):
    """Domain exception raised when an API key is not found"""

    def __init__(self, message: str = "API key not found") -> None:
        super().__init__(message)

