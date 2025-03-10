import uuid as uuid_pkg
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedSchema(BaseModel, Generic[T]):
    count: int
    data: list[T]


class UUIDSchema(BaseModel):
    id: uuid_pkg.UUID


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class Status(BaseModel):
    detail: str
