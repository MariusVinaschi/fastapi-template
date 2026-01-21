"""
User domain models - Framework agnostic SQLAlchemy models.
"""

from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.base.authorization import AuthorizationContext
from app.domains.base.models import Base, CreatedByMixin, TimestampMixin, UUIDMixin

RoleUser = Literal["standard", "admin"]


class User(Base, UUIDMixin, TimestampMixin, CreatedByMixin):
    """User entity - core domain model"""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column("email", unique=True, nullable=False, index=True)
    role: Mapped[RoleUser] = mapped_column(
        Enum(
            "standard",
            "admin",
            name="role",
            create_constraint=True,
            validate_strings=True,
        ),
        default="standard",
    )
    clerk_id: Mapped[str] = mapped_column("clerk_id", nullable=True, index=True)

    api_key: Mapped[Optional["APIKey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __str__(self) -> str:
        return f"{self.email}"


class APIKey(Base, UUIDMixin, TimestampMixin):
    """API Key entity for user authentication"""

    __tablename__ = "api_keys"

    key_hash: Mapped[str] = mapped_column("key_hash", nullable=False, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)

    user: Mapped["User"] = relationship(back_populates="api_key")


class UserAuthorizationAdapter(AuthorizationContext):
    """
    Adapter that converts a User model to an AuthorizationContext.
    This allows the domain services to work with authorization without
    knowing about the specific User implementation.
    """

    def __init__(self, user: User):
        self._user = user

    @property
    def user_id(self) -> str:
        return str(self._user.id)

    @property
    def user_email(self) -> str:
        return self._user.email

    @property
    def user_role(self) -> RoleUser:
        return self._user.role
