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
from app.domains.users.schemas import APIKeyCreate, APIKeyGenerated, ClerkUserUpdate, RoleEnum, UserCreate
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


class ClerkUserService(
    UserService,
):
    @staticmethod
    def _extract_primary_email(data: dict) -> str:
        """Find the primary email from Clerk's payload."""
        primary_email_id = data.get("primary_email_address_id")
        email_entries = data.get("email_addresses")

        if email_entries is None:
            raise ValueError("email_addresses not found in the Clerk payload")

        if len(email_entries) == 1:
            return email_entries[0].get("email_address")

        obj = next((obj for obj in email_entries if obj.get("id") == primary_email_id), None)
        if not obj:
            raise ValueError("Primary email address not found in the Clerk payload")

        return obj.get("email_address")

    @staticmethod
    def _check_clerk_id(data: dict) -> str:
        if not data.get("id"):
            raise ValueError("Missing clerk id")
        return data["id"]

    async def create_user(self, data: dict) -> User:
        clerk_id = self._check_clerk_id(data)
        primary_email = self._extract_primary_email(data)
        user_service = self.for_system(self.session)

        try:
            user = await self.get_by_clerk_id(clerk_id)
            if user.email != primary_email:
                return await user_service.update(user.id, ClerkUserUpdate(email=primary_email))
            return user
        except UserNotFoundException:
            pass

        try:
            await self.get_by_email(primary_email)
            raise ValueError(f"User with email {primary_email} already exists")
        except UserNotFoundException:
            return await self.for_system(self.session).create(
                UserCreate(
                    email=primary_email,
                    clerk_id=clerk_id,
                )
            )

    async def update_user(self, data: dict) -> User:
        clerk_id = self._check_clerk_id(data)
        user_service = self.for_system(self.session)
        user = await self.get_by_clerk_id(clerk_id)

        primary_email = self._extract_primary_email(data)
        if primary_email != user.email:
            await user_service.update(user.id, ClerkUserUpdate(email=primary_email))

        return user

    async def delete_user(self, data: dict) -> bool:
        clerk_id = self._check_clerk_id(data)
        user_service = self.for_system(self.session)
        user = await user_service.get_by_clerk_id(clerk_id)
        await self.delete(user.id)
        return True


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
