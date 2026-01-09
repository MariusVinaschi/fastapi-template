"""
Domain exceptions - Framework agnostic.
These exceptions are raised by domain services and should be
caught and transformed by the delivery layer (API, workers, etc.)
"""


class DomainException(Exception):
    """Base exception for all domain errors"""

    def __init__(self, message: str = "Domain error"):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found in the database"""

    def __init__(self, message: str = "Entity not found"):
        super().__init__(message)


class PermissionDenied(DomainException):
    """Raised when a user doesn't have permission to perform an action"""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)


class ValidationError(DomainException):
    """Raised when validation fails"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message)

