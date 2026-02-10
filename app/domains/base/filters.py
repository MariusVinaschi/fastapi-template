"""
Filter parameters - Framework agnostic.
These are pure Pydantic models for filtering and pagination.
"""

from pydantic import BaseModel, ConfigDict, Field


class BaseFilterParams(BaseModel):
    """Base filter parameters for list operations"""

    limit: int = Field(default=10, ge=1, le=100, description="Number of items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    search: str | None = Field(default=None, description="Search query")
    order_by: str | None = Field(default=None, description="Field to order by")
    id__in: list[str] | None = Field(default=None, description="Filter by IDs")

    model_config = ConfigDict(extra="forbid")
