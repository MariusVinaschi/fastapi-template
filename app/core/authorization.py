from abc import ABC, abstractmethod
from typing import Generic, Protocol, TypeVar

from sqlalchemy import Select

from app.core.models import Base


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


class OrganizationAware(Protocol):
    """
    Interface for contexts that support the concept of organization.

    This interface can be implemented by any class that wants to add
    an organization context, without requiring explicit inheritance
    (thanks to the use of Protocol).
    """

    @property
    def organization_id(self) -> str:
        """The organization identifier in the current context"""
        pass


class OrganizationAuthorizationContext(AuthorizationContext, OrganizationAware):
    """
    Concrete implementation for B2B applications with organization context.

    This class combines the base AuthorizationContext interface with
    the OrganizationAware interface to provide a complete context
    for applications that require an organizational dimension.
    """

    def __init__(
        self, user_id: str, user_email: str, user_role: str, organization_id: str
    ):
        self._user_id = user_id
        self._user_email = user_email
        self._user_role = user_role
        self._organization_id = organization_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def user_email(self) -> str:
        return self._user_email

    @property
    def user_role(self) -> str:
        return self._user_role

    @property
    def organization_id(self) -> str:
        return self._organization_id


# Generic type for scope strategies
T = TypeVar("T", bound=Base)


class AuthorizationScopeStrategy(ABC, Generic[T]):
    """
    Base strategy for applying scope restrictions to queries.

    This abstract class defines the interface for all scope strategies
    that filter query results based on the authorization context.
    """

    def __init__(self, model: type[T]):
        self.model = model

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        """
        Apply scope with a validated context.

        Args:
            query: The SQL query to filter
            context: The authorization context containing user information

        Returns:
            The filtered query according to the strategy
        """
        return query


class OrganizationScopeStrategy(AuthorizationScopeStrategy[T]):
    """
    Strategy that filters results based on organization_id.

    This strategy checks if the context implements the OrganizationAware interface
    and, if so, filters the results to show only those belonging to the user's
    organization.
    """

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        """
        Apply an organization filter to the query if applicable.

        Args:
            query: The SQL query to filter
            context: The authorization context

        Returns:
            The query filtered by organization_id if the context allows it
        """
        # Check if the context implements OrganizationAware
        if isinstance(context, OrganizationAware):
            # Check if the model has an organization_id attribute
            if hasattr(self.model, "organization_id"):
                return query.where(
                    self.model.organization_id == context.organization_id
                )

        return query
