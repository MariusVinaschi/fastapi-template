"""
Refresh session models - Framework agnostic SQLAlchemy models.

A ``RefreshSession`` is the server-side record of an issued refresh token. Only the
SHA-256 hash of the token is stored (never the token itself), so a database leak does
not expose usable refresh tokens. Rotation groups successive tokens under a shared
``family_id`` to enable reuse detection (a replayed, already-used token revokes the
whole family). See ``sessions/service.py`` for the rotation logic.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.base.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.domains.users.models import User


class RefreshSession(Base, UUIDMixin, TimestampMixin):
    """Server-side record of an issued refresh token (stored hashed)."""

    __tablename__ = "refresh_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column("token_hash", nullable=False, unique=True, index=True)
    family_id: Mapped[UUID] = mapped_column("family_id", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column("expires_at", DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column("used_at", DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column("revoked_at", DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User")
