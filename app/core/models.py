import uuid
from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = MetaData(naming_convention=convention)

    def __repr__(self) -> str:
        columns = ", ".join(
            [
                f"{k}={repr(v)}"
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            ]
        )
        return f"<{self.__class__.__name__}({columns})>"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column("created_at", default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", default=datetime.now(), onupdate=datetime.now()
    )


class CreatedByMixin:
    created_by: Mapped[str] = mapped_column("created_by", nullable=False)
    updated_by: Mapped[str] = mapped_column("updated_by", nullable=False)


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        "id", UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )
