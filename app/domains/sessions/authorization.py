"""
Refresh session authorization strategy - Framework agnostic.

Refresh sessions are managed exclusively through system operations (auth flows), so
this scope strategy is defensive only: if ever accessed in a user context, a user can
see solely their own sessions.
"""

from sqlalchemy import Select

from app.domains.base.authorization import AuthorizationContext, AuthorizationScopeStrategy
from app.domains.sessions.models import RefreshSession


class RefreshSessionScopeStrategy(AuthorizationScopeStrategy):
    def __init__(self):
        super().__init__(RefreshSession)

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        return query.where(self.model.user_id == context.user_id)
