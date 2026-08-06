"""
Refresh session repository - Framework agnostic data access.

Composes the base Create/Update/Read mixins and adds only the two operations the
generic CRUD layer doesn't cover: lookup by token hash and family-wide revocation.
Follows the Unit-of-Work rule inherited from the mixins: mutations flush, never commit.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.repository import (
    CreateRepositoryMixin,
    ReadRepositoryMixin,
    UpdateRepositoryMixin,
)
from app.domains.sessions.authorization import RefreshSessionScopeStrategy
from app.domains.sessions.models import RefreshSession


class RefreshSessionRepository(
    CreateRepositoryMixin,
    UpdateRepositoryMixin,
    ReadRepositoryMixin,
):
    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(session, RefreshSessionScopeStrategy(), RefreshSession, authorization_context)

    async def find_by_hash(self, token_hash: str) -> RefreshSession | None:
        query = select(self.model).where(self.model.token_hash == token_hash)
        query = self._apply_user_scope(query)
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def revoke_family(self, family_id: UUID) -> int:
        """Revoke every still-active token in a family in one statement.

        Uses synchronize_session="fetch" so any family rows already loaded in the
        current session (e.g. a sibling token) reflect the revocation immediately,
        not just the database.
        """
        stmt = (
            sa_update(self.model)
            .where(self.model.family_id == family_id, self.model.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return getattr(result, "rowcount", 0) or 0
