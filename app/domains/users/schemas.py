"""
User schemas - Framework agnostic Pydantic models.
These are pure DTOs with no delivery layer dependencies.
"""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.domains.base.schemas import TimestampSchema, UUIDSchema


class RoleEnum(str, Enum):
    """User role enumeration"""

    ADMIN = "admin"
    STANDARD = "standard"


class UserEmail(BaseModel):
    """Base schema with email"""

    email: EmailStr


class UserBase(UserEmail):
    """Base user schema with role"""

    role: RoleEnum = RoleEnum.STANDARD


class UserRead(UserBase, UUIDSchema, TimestampSchema):
    """Schema for reading user data"""
    pass


class UserCreate(UserBase):
    """Schema for creating a user"""

    clerk_id: str


class UserPatch(BaseModel):
    """Schema for updating a user (partial update)"""

    role: Optional[RoleEnum] = None


class UserConfigurationPatch(BaseModel):
    """Schema for updating user configuration"""

    configuration: dict


class ClerkUserUpdate(BaseModel):
    """Schema for Clerk webhook user updates"""

    email: EmailStr


# API Key schemas
class APIKeyGenerated(BaseModel):
    """Schema returned when generating a new API key"""

    api_key: str


class APIKeyCreate(BaseModel):
    """Internal schema for creating an API key"""

    user_id: UUID
    key_hash: str

