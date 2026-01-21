"""
Authorization abstractions - Framework agnostic.
Defines the interfaces for authorization contexts and scope strategies.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

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
    """

    def __init__(self, model: type[T] = None):
        self.model = model

    def apply_scope(self, query: Select, context: Optional[AuthorizationContext]) -> Select:
        """
        Apply scope with an optional context.

        Args:
            query: The SQL query to filter
            context: The authorization context containing user information,
                    None for system operations

        Returns:
            The filtered query according to the strategy
        """
        # If no context provided (system operation), return unfiltered query
        if context is None:
            return query
        return query
