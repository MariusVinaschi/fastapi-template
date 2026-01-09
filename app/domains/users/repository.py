"""
User repository - Framework agnostic data access layer.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.repository import (
    CreateRepositoryMixin,
    DeleteRepositoryMixin,
    ListRepositoryMixin,
    ReadRepositoryMixin,
    UpdateRepositoryMixin,
)
from app.domains.users.authorization import UserScopeStrategy, APIKeyScopeStrategy
from app.domains.users.models import User, APIKey


class UserRepository(
    CreateRepositoryMixin,
    UpdateRepositoryMixin,
    DeleteRepositoryMixin,
    ReadRepositoryMixin,
    ListRepositoryMixin,
):
    """Repository for User entity operations"""

    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(session, UserScopeStrategy(), User, authorization_context)

    async def find_by_email(
        self,
        email: str,
    ) -> User | None:
        """Find a user by their email address"""
        instance = await self.session.scalars(select(self.model).where(self.model.email == email))
        return instance.one_or_none()


class APIKeyRepository(
    ReadRepositoryMixin,
    CreateRepositoryMixin,
    DeleteRepositoryMixin,
):
    """Repository for APIKey entity operations"""

    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(session, APIKeyScopeStrategy(), APIKey, authorization_context)

    async def get_by_user_id(self, user_id: UUID) -> APIKey | None:
        """Get API key by user ID with user relationship loaded"""
        instance = await self.session.scalars(
            select(self.model)
            .options(joinedload(self.model.user))
            .where(self.model.user_id == user_id)
        )
        return instance.one_or_none()

    async def get_by_api_key_hash(self, api_key_hash: str) -> APIKey | None:
        """Get API key by its hash with user relationship loaded"""
        instance = await self.session.scalars(
            select(self.model)
            .options(joinedload(self.model.user))
            .where(self.model.key_hash == api_key_hash)
        )
        return instance.one_or_none()

