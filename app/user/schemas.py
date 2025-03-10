from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.core.schemas import TimestampSchema, UUIDSchema


class RoleEnum(str, Enum):
    MANAGER = "manager"
    STANDARD = "standard"


class UserEmail(BaseModel):
    email: EmailStr


class UserBase(UserEmail):
    first_name: str
    last_name: str
    role: RoleEnum = "standard"


class UserRead(UserBase, UUIDSchema, TimestampSchema):
    pass


class UserCreate(UserBase):
    pass


class UserPatch(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_verify: Optional[bool] = None
    role: Optional[RoleEnum] = None

