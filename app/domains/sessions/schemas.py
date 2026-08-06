"""
Refresh session schemas - Framework agnostic Pydantic DTOs.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RefreshSessionCreate(BaseModel):
    """Internal schema for persisting a refresh session (token already hashed)."""

    user_id: UUID
    token_hash: str
    family_id: UUID
    expires_at: datetime
