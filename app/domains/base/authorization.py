"""
Authorization abstractions - Framework agnostic.
Defines the interfaces for authorization contexts and scope strategies.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy import Select

from app.domains.base.models import Base


class AuthorizationContext(ABC):
    """
    Base interface for all authorization contexts.

    This class defines the minimum information required to perform
    authorization checks in the application. Any concrete implementation
    must provide at least these basic user information.
    """

    @property
    @abstractmethod
    def user_id(self) -> str:
        """Unique identifier of the user"""
        pass

    @property
    @abstractmethod
    def user_email(self) -> str:
        """Email address of the user"""
        pass

    @property
    @abstractmethod
    def user_role(self) -> str:
        """User's role in the system"""
        pass


# Generic type for scope strategies
T = TypeVar("T", bound=Base)


class AuthorizationScopeStrategy(ABC, Generic[T]):
    """
    Base strategy for applying scope restrictions to queries.

    This abstract class defines the interface for all scope strategies
    that filter query results based on the authorization context.

    Note: apply_scope always receives a non-None context. The None-check
    is handled by the repository's _apply_user_scope method, which decides
    IF scope should be applied. This strategy only decides HOW to apply it.
    """

    def __init__(self, model: type[T]):
        self.model = model

    @abstractmethod
    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        """
        Apply scope filtering to a query for the given user context.

        This method is only called for user operations (never for system operations).
        The repository layer handles the system/user distinction before calling this.

        Args:
            query: The SQL query to filter
            context: The authorization context containing user information (never None)

        Returns:
            The filtered query according to the strategy
        """
        ...
