"""
User schemas - Framework agnostic Pydantic models.
These are pure DTOs with no delivery layer dependencies.
"""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.domains.base.schemas import TimestampSchema, UUIDSchema


class RoleEnum(StrEnum):
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
    """Internal schema for persisting a user (password already hashed)."""

    password_hash: str


class UserLogin(UserEmail):
    """Schema for email + password login."""

    password: str


class UserPatch(BaseModel):
    """Schema for updating a user (partial update)"""

    role: RoleEnum | None = None


class UserConfigurationPatch(BaseModel):
    """Schema for updating user configuration"""

    configuration: dict


class TokenPair(BaseModel):
    """Access + refresh tokens returned to header-based clients."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# API Key schemas
class APIKeyGenerated(BaseModel):
    """Schema returned when generating a new API key"""

    api_key: str


class APIKeyCreate(BaseModel):
    """Internal schema for creating an API key"""

    user_id: UUID
    key_hash: str
