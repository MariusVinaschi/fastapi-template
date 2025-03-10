from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BaseFilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    search: Optional[str] = None
    order_by: Optional[str] = None
    id__in: Optional[list[str]] = None

    @classmethod
    def get_allowed_order_by_fields(cls) -> list[str]:
        return []

    @field_validator("order_by")
    def validate_order_by(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        field = value
        if value.startswith("-") or value.startswith("+"):
            field = value[1:]

        allowed_fields = cls.get_allowed_order_by_fields()

        if not allowed_fields:
            return value

        if field not in allowed_fields:
            raise ValueError(
                f"Invalid order_by field. Must be one of: {allowed_fields}"
            )

        return value

    @classmethod
    def split_string_to_list(cls, value):
        if isinstance(value, list) and len(value) == 1 and "," in value[0]:
            return [v.strip() for v in value[0].split(",")]
        return value

    @field_validator("id__in", mode="before")
    def transform_value(cls, value):
        return cls.split_string_to_list(value)
