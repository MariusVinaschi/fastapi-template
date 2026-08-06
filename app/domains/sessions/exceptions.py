"""
Refresh session domain exceptions - Framework agnostic.
Mapped to HTTP 401 by the delivery layer.
"""

from app.domains.base.exceptions import DomainException, EntityNotFoundException


class RefreshSessionNotFoundException(EntityNotFoundException):
    """Raised when a refresh session cannot be found."""

    def __init__(self, message: str = "Refresh session not found") -> None:
        super().__init__(message)


class InvalidRefreshTokenError(DomainException):
    """Raised when a refresh token is unknown, expired, or revoked."""

    def __init__(self, message: str = "Invalid refresh token") -> None:
        super().__init__(message)


class RefreshTokenReuseError(DomainException):
    """Raised when an already-used refresh token is replayed (theft signal)."""

    def __init__(self, message: str = "Refresh token reuse detected") -> None:
        super().__init__(message)
