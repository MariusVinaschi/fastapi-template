import hashlib
import hmac
import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.exceptions import PermissionDenied
from app.domains.base.service import (
    CreateServiceMixin,
    DeleteServiceMixin,
    ListServiceMixin,
    UpdateServiceMixin,
)
from app.domains.users.exceptions import APIKeyNotFoundException, UserNotFoundException
from app.domains.users.models import APIKey, User
from app.domains.users.repository import APIKeyRepository, UserRepository
from app.domains.users.schemas import APIKeyCreate, APIKeyGenerated, RoleEnum
from app.infrastructure.config import settings


class UserService(
    ListServiceMixin[User, UserRepository],
    UpdateServiceMixin[User, UserRepository],
    CreateServiceMixin[User, UserRepository],
    DeleteServiceMixin[User, UserRepository],
):
    repository_class = UserRepository
    not_found_exception = UserNotFoundException

    def _check_general_permissions(self, action: str) -> bool:
        """Check general permissions for user operations"""
        # System operations bypass all permission checks
        if self._is_system_operation():
            return True

        assert self.authorization_context is not None
        # Admins can do everything
        if self.authorization_context.user_role == RoleEnum.ADMIN:
            return True

        # Regular users can read and update
        if action in ["update", "read"]:
            return True

        raise PermissionDenied("Action not allowed")

    def _check_instance_permissions(self, action: str, instance: User) -> bool:
        """Check instance-level permissions for user operations"""
        # System operations bypass all permission checks
        if self._is_system_operation():
            return True

        assert self.authorization_context is not None
        # Users cannot delete themselves
        if action == "delete" and self.authorization_context.user_id == str(instance.id):
            raise PermissionDenied("Action not allowed")

        # Admins can do everything
        if self.authorization_context.user_role == RoleEnum.ADMIN:
            return True

        # Regular users can only access their own data
        if action in ["update", "read"] and self.authorization_context.user_id == str(instance.id):
            return True

        raise PermissionDenied("Action not allowed")

    async def get_by_email(self, email: str) -> User:
        """Get user by email with access control"""
        self._check_general_permissions("read")

        user = await self.repository.find_by_email(email=email)
        if not user:
            raise UserNotFoundException

        self._check_instance_permissions("read", user)

        return user

    async def get_by_clerk_id(self, clerk_id: str) -> User:
        """Get user by Clerk ID with access control"""
        self._check_general_permissions("read")

        user = await self.repository.find_by_clerk_id(clerk_id)
        if not user:
            raise UserNotFoundException

        self._check_instance_permissions("read", user)

        return user


class APIKeyService(
    CreateServiceMixin[APIKey, APIKeyRepository],
    DeleteServiceMixin[APIKey, APIKeyRepository],
):
    repository_class = APIKeyRepository
    not_found_exception = APIKeyNotFoundException

    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(session, authorization_context)
        # Use HMAC-SHA256 for API key hashing - deterministic and secure
        self.secret_key = settings.SECRET_KEY.encode("utf-8")

    def _prepare_create_data(self, data: APIKeyCreate) -> dict:
        return data.model_dump()

    async def get_by_user_id(self, user_id: UUID) -> APIKey:
        self._check_general_permissions("read")

        api_key = await self.repository.get_by_user_id(user_id)
        if not api_key:
            raise APIKeyNotFoundException

        self._check_instance_permissions("read", api_key)

        return api_key

    async def get_by_api_key_hash(self, api_key_hash: str) -> APIKey:
        self._check_general_permissions("read")

        api_key = await self.repository.get_by_api_key_hash(api_key_hash)
        if not api_key:
            raise APIKeyNotFoundException

        self._check_instance_permissions("read", api_key)

        return api_key

    async def generate_api_key(self, user: User) -> APIKeyGenerated:
        try:
            existing_api_key = await self.get_by_user_id(user.id)
            await self.delete(existing_api_key.id)
        except APIKeyNotFoundException:
            pass

        api_key = f"{secrets.token_urlsafe(32)}"
        key_hash = self.hash_api_key(api_key)

        await self.create(
            APIKeyCreate(
                user_id=user.id,
                key_hash=key_hash,
            )
        )

        return APIKeyGenerated(api_key=api_key)

    async def revoke_api_key(self, user: User) -> bool:
        api_key = await self.get_by_user_id(user.id)
        await self.delete(api_key.id)
        return True

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage using HMAC-SHA256 - deterministic and searchable"""
        return hmac.new(self.secret_key, api_key.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash using HMAC-SHA256"""
        expected_hash = self.hash_api_key(api_key)
        return hmac.compare_digest(expected_hash, hashed_key)
