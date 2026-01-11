from sqlalchemy.orm import Mapped, mapped_column

from app.domains.base.models import Base, CreatedByMixin, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    User model representing a user in the system.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column("email", nullable=False, unique=True)
    role: Mapped[str] = mapped_column("role", nullable=False)


class TestModel(Base, UUIDMixin, TimestampMixin, CreatedByMixin):
    """
    Test model representing a typical business entity.
    Includes basic fields
    """

    __tablename__ = "test_models"

    name: Mapped[str] = mapped_column("name", nullable=False)
