"""
User authorization strategies - Framework agnostic.
Defines how user-related queries should be scoped.
"""

from sqlalchemy import Select

from app.domains.base.authorization import (
    AuthorizationContext,
    AuthorizationScopeStrategy,
)
from app.domains.users.models import APIKey, User


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
