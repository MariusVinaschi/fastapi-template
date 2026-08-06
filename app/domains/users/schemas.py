"""
User schemas - Framework agnostic Pydantic models.
These are pure DTOs with no delivery layer dependencies.
"""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domains.base.schemas import TimestampSchema, UUIDSchema

# Minimum password length enforced at registration.
PASSWORD_MIN_LENGTH = 8


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


class UserRegister(UserEmail):
    """Schema for self-registration (plaintext password, validated then hashed)."""

    password: str = Field(min_length=PASSWORD_MIN_LENGTH)


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
