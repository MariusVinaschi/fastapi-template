from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domains.base.repository import (
    CreateRepositoryMixin,
    DeleteRepositoryMixin,
    ListRepositoryMixin,
    ReadRepositoryMixin,
    UpdateRepositoryMixin,
)
from app.domains.users.authorization import APIKeyScopeStrategy, UserScopeStrategy
from app.domains.users.models import APIKey, User


class UserRepository(
    CreateRepositoryMixin,
    UpdateRepositoryMixin,
    DeleteRepositoryMixin,
    ReadRepositoryMixin,
    ListRepositoryMixin,
):
    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(session, UserScopeStrategy(), User, authorization_context)

    async def find_by_email(
        self,
        email: str,
    ) -> User | None:
        instance = await self.session.scalars(select(self.model).where(self.model.email == email))
        return instance.one_or_none()

    async def find_by_clerk_id(self, clerk_id: str) -> User | None:
        instance = await self.session.scalars(select(self.model).where(self.model.clerk_id == clerk_id))
        return instance.one_or_none()


class APIKeyRepository(
    ReadRepositoryMixin,
    CreateRepositoryMixin,
    DeleteRepositoryMixin,
):
    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(session, APIKeyScopeStrategy(), APIKey, authorization_context)

    async def get_by_user_id(self, user_id: UUID) -> APIKey | None:
        instance = await self.session.scalars(
            select(self.model).options(joinedload(self.model.user)).where(self.model.user_id == user_id)
        )
        return instance.one_or_none()

    async def get_by_api_key_hash(self, api_key_hash: str) -> APIKey | None:
        instance = await self.session.scalars(
            select(self.model).options(joinedload(self.model.user)).where(self.model.key_hash == api_key_hash)
        )
        return instance.one_or_none()
