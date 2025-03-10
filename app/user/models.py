from typing import Literal

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.authorization import AuthorizationContext
from app.core.models import Base, CreatedByMixin, TimestampMixin, UUIDMixin

RoleUser = Literal["manager", "standard"]


class User(Base, UUIDMixin, TimestampMixin, CreatedByMixin):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column("email", unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column("first_name", nullable=False)
    last_name: Mapped[str] = mapped_column("last_name", nullable=False)
    role: Mapped[RoleUser] = mapped_column(
        Enum(
            "manager",
            "standard",
            name="role",
            create_constraint=True,
            validate_strings=True,
        ),
        default="standard",
    )

    def __str__(self) -> str:
        return f"{self.email}"


class UserAuthorizationAdapter(AuthorizationContext):
    def __init__(self, user):
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
