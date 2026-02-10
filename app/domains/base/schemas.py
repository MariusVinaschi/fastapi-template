"""
Base schemas - Framework agnostic Pydantic models.
These are pure data transfer objects with no framework dependencies.
"""

from datetime import datetime
from typing import Generic, List, TypeVar
from uuid import UUID

from pydantic import BaseModel


class UUIDSchema(BaseModel):
    """Schema mixin for UUID field"""

    id: UUID


class TimestampSchema(BaseModel):
    """Schema mixin for timestamp fields"""

    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class PaginatedSchema(BaseModel, Generic[T]):
    """Generic paginated response schema"""

    count: int
    data: List[T]


class Status(BaseModel):
    """Simple status response"""

    detail: str
