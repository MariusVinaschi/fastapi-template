from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import (
    CreateRepositoryMixin,
    DeleteRepositoryMixin,
    ListRepositoryMixin,
    ReadRepositoryMixin,
    UpdateRepositoryMixin,
)
from app.user.authorization import UserScopeStrategy
from app.user.models import User


class UserRepository(
    CreateRepositoryMixin,
    UpdateRepositoryMixin,
    DeleteRepositoryMixin,
    ReadRepositoryMixin,
    ListRepositoryMixin,
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserScopeStrategy(), User)

    async def find_by_email(
        self,
        email: str,
    ) -> User | None:
        instance = await self.session.scalars(
            select(self.model).where(self.model.email == email)
        )
        return instance.one_or_none()
