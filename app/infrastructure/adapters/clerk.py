"""
Clerk webhook adapter.
Translates Clerk event payloads into domain operations on UserService.
This is an infrastructure adapter — it knows about Clerk's payload format
so the domain layer doesn't have to.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.models import User
from app.domains.users.schemas import ClerkUserUpdate, UserCreate
from app.domains.users.service import UserService


class ClerkWebhookAdapter:
    """
    Adapter between Clerk webhook events and the UserService domain layer.

    Responsibilities:
    - Parse and validate Clerk-specific payload structure
    - Map Clerk events to UserService domain operations
    - Handle idempotency (create vs update on user.created)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._service = UserService.for_system(session)

    @classmethod
    def for_system(cls, session: AsyncSession) -> "ClerkWebhookAdapter":
        return cls(session)

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

        try:
            user = await self._service.get_by_clerk_id(clerk_id)
            if user.email != primary_email:
                return await self._service.update(user.id, ClerkUserUpdate(email=primary_email))
            return user
        except UserNotFoundException:
            pass

        try:
            await self._service.get_by_email(primary_email)
            raise ValueError(f"User with email {primary_email} already exists")
        except UserNotFoundException:
            return await self._service.create(
                UserCreate(
                    email=primary_email,
                    clerk_id=clerk_id,
                )
            )

    async def update_user(self, data: dict) -> User:
        clerk_id = self._check_clerk_id(data)
        user = await self._service.get_by_clerk_id(clerk_id)

        primary_email = self._extract_primary_email(data)
        if primary_email != user.email:
            await self._service.update(user.id, ClerkUserUpdate(email=primary_email))

        return user

    async def delete_user(self, data: dict) -> bool:
        clerk_id = self._check_clerk_id(data)
        user = await self._service.get_by_clerk_id(clerk_id)
        await self._service.delete(user.id)
        return True
