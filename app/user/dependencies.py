from typing import Annotated

from fastapi import Depends

from app.core.authorization import AuthorizationContext
from app.security import auth
from app.user.models import User, UserAuthorizationAdapter

CurrentUser = Annotated[User, Depends(auth.get_current_user)]

CurrentManagerUser = Annotated[User, Depends(auth.get_current_manager_user)]


def get_auth_context(
    user: User = Depends(auth.get_current_user),
) -> AuthorizationContext:
    return UserAuthorizationAdapter(user)


def get_manager_auth_context(
    user: User = Depends(auth.get_current_manager_user),
) -> AuthorizationContext:
    return UserAuthorizationAdapter(user)


CurrentAuthContext = Annotated[AuthorizationContext, Depends(get_auth_context)]
CurrentManagerAuthContext = Annotated[
    AuthorizationContext, Depends(get_manager_auth_context)
]
