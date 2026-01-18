from sqlalchemy.orm import Mapped, mapped_column

from app.domains.base.models import Base, CreatedByMixin, TimestampMixin, UUIDMixin


class TestUser(Base, UUIDMixin, TimestampMixin):
    """
    Test user model for testing purposes.
    Named differently to avoid conflict with app.domains.users.models.User
    """

    __tablename__ = "test_users"

    email: Mapped[str] = mapped_column("email", nullable=False, unique=True)
    role: Mapped[str] = mapped_column("role", nullable=False)


class TestModel(Base, UUIDMixin, TimestampMixin, CreatedByMixin):
    """
    Test model representing a typical business entity.
    Includes basic fields
    """

    __tablename__ = "test_models"

    name: Mapped[str] = mapped_column("name", nullable=False)
