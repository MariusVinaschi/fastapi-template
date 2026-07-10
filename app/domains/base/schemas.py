"""
Base schemas - Framework agnostic Pydantic models.
These are pure data transfer objects with no framework dependencies.
"""

from datetime import datetime
from typing import Generic, List, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UUIDSchema(BaseModel):
    """Schema mixin for UUID field"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID


class TimestampSchema(BaseModel):
    """Schema mixin for timestamp fields"""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime


class CreatedByAndUpdatedBySchema(BaseModel):
    """Schema mixin for created_by and updated_by fields"""

    model_config = ConfigDict(from_attributes=True)

    created_by: str
    updated_by: str


T = TypeVar("T")


class PaginatedSchema(BaseModel, Generic[T]):
    """Generic paginated response schema"""

    count: int
    data: List[T]


class Status(BaseModel):
    """Simple status response"""

    detail: str
