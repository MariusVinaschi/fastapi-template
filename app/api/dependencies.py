"""
FastAPI dependencies - Framework specific dependency injection.
These dependencies bridge the domain layer with FastAPI's DI system.
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.infrastructure.security import auth
from app.domains.base.authorization import AuthorizationContext
from app.domains.users.models import User, UserAuthorizationAdapter

# Session dependency
CurrentSession = Annotated[AsyncSession, Depends(get_session)]

# User dependencies
CurrentUser = Annotated[User, Depends(auth.get_current_user)]
CurrentAdminUser = Annotated[User, Depends(auth.get_current_admin_user)]


def get_auth_context(
    user: User = Depends(auth.get_current_user),
) -> AuthorizationContext:
    """Get authorization context from authenticated user"""
    return UserAuthorizationAdapter(user)


def get_admin_auth_context(
    user: User = Depends(auth.get_current_admin_user),
) -> AuthorizationContext:
    """Get authorization context from authenticated admin user"""
    return UserAuthorizationAdapter(user)


# Authorization context dependencies
CurrentAuthContext = Annotated[AuthorizationContext, Depends(get_auth_context)]
CurrentAdminAuthContext = Annotated[AuthorizationContext, Depends(get_admin_auth_context)]

