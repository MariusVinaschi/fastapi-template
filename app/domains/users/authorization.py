"""
User authorization strategies and context adapters - Framework agnostic.
Defines how user-related queries should be scoped, and how a User entity
is mapped to an AuthorizationContext.
"""

from sqlalchemy import Select

from app.domains.base.authorization import (
    AuthorizationContext,
    AuthorizationScopeStrategy,
)
from app.domains.users.models import APIKey, RoleUser, User


class UserAuthorizationAdapter(AuthorizationContext):
    """
    Adapter that converts a User model to an AuthorizationContext.
    Lives here alongside the scope strategies, keeping all authorization
    concerns for the users domain in one place.
    """

    def __init__(self, user: User):
        self._user = user

    @property
    def user_id(self) -> str:
        return str(self._user.id)

    @property
    def user_email(self) -> str:
        return self._user.email

    @property
    def user_role(self) -> RoleUser:
        return self._user.role


class UserScopeStrategy(AuthorizationScopeStrategy):
    """
    Scope strategy for User entities.
    Users are globally visible to all authenticated users.
    """

    def __init__(self):
        super().__init__(User)

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        # Users are visible to all authenticated users
        return query


class APIKeyScopeStrategy(AuthorizationScopeStrategy):
    """
    Scope strategy for APIKey entities.
    API keys are only visible to their owner.
    """

    def __init__(self):
        super().__init__(APIKey)

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        # API keys are scoped to the user who owns them
        return query.where(self.model.user_id == context.user_id)
