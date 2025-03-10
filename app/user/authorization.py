from sqlalchemy import Select

from app.core.authorization import (
    AuthorizationContext,
    AuthorizationScopeStrategy,
)
from app.user.models import User


class UserScopeStrategy(AuthorizationScopeStrategy):
    def __init__(self):
        super().__init__(User)

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        return query
