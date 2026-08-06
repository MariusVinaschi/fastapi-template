"""
Refresh session service - Framework agnostic business logic.

Owns refresh-token rotation and reuse detection. Only ever used through
``RefreshSessionService.for_system(session)`` since refresh handling is not a
user-facing operation. Persistence reuses the base CreateServiceMixin (like
``APIKeyService``); only the rotation state machine lives here.
"""

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domains.base.service import CreateServiceMixin
from app.domains.sessions.exceptions import (
    InvalidRefreshTokenError,
    RefreshSessionNotFoundException,
    RefreshTokenReuseError,
)
from app.domains.sessions.models import RefreshSession
from app.domains.sessions.repository import RefreshSessionRepository
from app.domains.sessions.schemas import RefreshSessionCreate


def hash_refresh_token(token: str) -> str:
    """Deterministic SHA-256 hash used to look up a refresh token without storing it."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RefreshSessionService(CreateServiceMixin[RefreshSession, RefreshSessionRepository]):
    repository_class = RefreshSessionRepository
    not_found_exception = RefreshSessionNotFoundException

    def _prepare_create_data(self, data: RefreshSessionCreate) -> dict:
        # RefreshSession has no created_by/updated_by audit columns (system-managed).
        return data.model_dump()

    async def issue(
        self,
        user_id: UUID,
        refresh_token: str,
        expires_at: datetime,
        family_id: UUID | None = None,
    ) -> RefreshSession:
        """Persist a freshly issued refresh token (new family unless one is supplied)."""
        return await self.create(
            RefreshSessionCreate(
                user_id=user_id,
                token_hash=hash_refresh_token(refresh_token),
                family_id=family_id or uuid4(),
                expires_at=expires_at,
            )
        )

    async def rotate(
        self,
        user_id: UUID,
        old_refresh_token: str,
        new_refresh_token: str,
        expires_at: datetime,
    ) -> RefreshSession:
        """
        Rotate a refresh token: invalidate the presented one and issue a successor in
        the same family. Replaying an already-used token revokes the whole family.
        """
        stored = await self.repository.find_by_hash(hash_refresh_token(old_refresh_token))

        if stored is None or stored.user_id != user_id or stored.revoked_at is not None:
            raise InvalidRefreshTokenError()

        if stored.expires_at <= datetime.now(UTC):
            raise InvalidRefreshTokenError()

        if stored.used_at is not None:
            # Already-rotated token replayed -> treat the whole family as compromised.
            await self.repository.revoke_family(stored.family_id)
            raise RefreshTokenReuseError()

        await self.repository.mark_used(stored)
        return await self.issue(
            user_id=stored.user_id,
            refresh_token=new_refresh_token,
            expires_at=expires_at,
            family_id=stored.family_id,
        )

    async def revoke(self, refresh_token: str) -> int:
        """Revoke the family of the given refresh token (logout). No-op if unknown."""
        stored = await self.repository.find_by_hash(hash_refresh_token(refresh_token))
        if stored is None:
            return 0
        return await self.repository.revoke_family(stored.family_id)
