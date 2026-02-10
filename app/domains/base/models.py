"""
Base ORM models - Framework agnostic SQLAlchemy models.
These are the foundation for all domain entities.
"""

import uuid
from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention for database constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models"""

    __abstract__ = True
    metadata = MetaData(naming_convention=convention)

    def __repr__(self) -> str:
        columns = ", ".join([f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith("_")])
        return f"<{self.__class__.__name__}({columns})>"


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at: Mapped[datetime] = mapped_column("created_at", default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column("updated_at", default=datetime.now, onupdate=datetime.now)


class UUIDMixin:
    """Mixin for UUID primary key"""

    id: Mapped[uuid.UUID] = mapped_column(
        "id", UUID(as_uuid=True), default=uuid.uuid4, primary_key=True  # type: ignore[no-matching-overload]
    )


class CreatedByMixin:
    """Mixin for tracking who created/updated the entity"""

    created_by: Mapped[str] = mapped_column("created_by", nullable=False)
    updated_by: Mapped[str] = mapped_column("updated_by", nullable=False)
