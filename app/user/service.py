from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import AuthorizationContext
from app.core.exceptions import PermissionDenied
from app.core.service import (
    CreateServiceMixin,
    DeleteServiceMixin,
    ListServiceMixin,
    UpdateServiceMixin,
)
from app.user.exceptions import UserNotFoundException
from app.user.models import User
from app.user.repository import UserRepository
from app.user.schemas import RoleEnum


class UserService(
    ListServiceMixin[User, UserRepository],
    UpdateServiceMixin[User, UserRepository],
    CreateServiceMixin[User, UserRepository],
    DeleteServiceMixin[User, UserRepository],
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserRepository, UserNotFoundException)

    def _check_general_permissions(
        self, action: str, authorization_context: AuthorizationContext
    ) -> bool:
        if authorization_context.user_role == RoleEnum.MANAGER:
            return True

        if action in ["read", "list"]:
            return True

        raise PermissionDenied("Action not allowed")

    def _check_instance_permissions(
        self,
        action: str,
        authorization_context: AuthorizationContext,
        instance: User,
    ) -> bool:
        if action == "delete" and authorization_context.user_id == str(instance.id):
            raise PermissionDenied("Action not allowed")

        return True

    async def get_by_email(
        self,
        email: str,
    ) -> User:
        user = await self.repository.find_by_email(
            email=email,
        )
        if not user:
            raise UserNotFoundException

        return user
