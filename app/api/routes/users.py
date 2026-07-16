"""
User management endpoints.
This module contains all user-related HTTP routes.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import (
    CurrentAdminAuthContext,
    CurrentAuthContext,
    CurrentSession,
    CurrentUser,
)
from app.api.exceptions import APIKeyNotFoundHTTPException, UserNotFoundHTTPException
from app.api.rate_limit import limiter
from app.domains.base.exceptions import PermissionDenied
from app.domains.base.schemas import PaginatedSchema, Status
from app.domains.users.exceptions import APIKeyNotFoundException, UserNotFoundException
from app.domains.users.filters import UserFilter
from app.domains.users.schemas import (
    APIKeyGenerated,
    UserCreate,
    UserPatch,
    UserRead,
)
from app.domains.users.service import APIKeyService, UserService

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

log = logging.getLogger(__name__)


@router.get("", response_model=PaginatedSchema[UserRead])
async def get_users(
    session: CurrentSession,
    authorization_context: CurrentAuthContext,
    filters: Annotated[UserFilter, Query()],
):
    """
    Get paginated list of users.
    Requires authentication.
    """
    return await UserService.for_user(session, authorization_context).get_paginated(filters)


@router.post("", response_model=UserRead)
async def create_user(
    data: UserCreate,
    authorization_context: CurrentAdminAuthContext,
    session: CurrentSession,
):
    """
    Create a new user.
    Requires admin privileges.
    """
    try:
        return await UserService.for_user(session, authorization_context).create(data)
    except IntegrityError as e:
        log.error(f"Error during the creation: {e}")
        raise HTTPException(status_code=400, detail="An user with this email already exist") from e
    except PermissionDenied as e:
        log.error(f"Error during the creation: {e}")
        raise HTTPException(status_code=403, detail="You are not allowed to create a user") from e
    except Exception as e:
        log.error(f"Error during the creation: {e}")
        raise HTTPException(status_code=400, detail="Error during the creation") from e


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
async def get_user(
    user_id: UUID,
    authorization_context: CurrentAuthContext,
    session: CurrentSession,
):
    """
    Get a specific user by ID.
    Requires authentication.
    """
    try:
        return await UserService.for_user(session, authorization_context).get_by_id(user_id)
    except UserNotFoundException as e:
        raise UserNotFoundHTTPException from e
    except PermissionDenied as e:
        raise UserNotFoundHTTPException from e


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserPatch,
    authorization_context: CurrentAdminAuthContext,
    session: CurrentSession,
):
    """
    Update a user.
    Requires admin privileges.
    """
    try:
        return await UserService.for_user(session, authorization_context).update(user_id, user_update)
    except UserNotFoundException as e:
        raise UserNotFoundHTTPException from e


@router.delete("/{user_id}", response_model=Status)
async def delete_user(
    user_id: UUID,
    session: CurrentSession,
    authorization_context: CurrentAdminAuthContext,
):
    """
    Delete a user.
    Requires admin privileges. Users cannot delete themselves.
    """
    try:
        await UserService.for_user(session, authorization_context).delete(user_id)
    except UserNotFoundException as e:
        raise UserNotFoundHTTPException from e
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail="You are not allowed to delete yourself") from e

    return Status(detail=f"Deleted user {user_id}")


# Me router - Current user operations
me_router = APIRouter(
    responses={404: {"description": "Not found"}},
)


@me_router.get("", response_model=UserRead)
async def read_users_me(current_user: CurrentUser):
    """
    Get the currently authenticated user's profile.
    """
    return current_user


@me_router.post("/api-key", response_model=APIKeyGenerated)
@limiter.limit("5/minute")
async def generate_api_key(
    request: Request,
    current_user: CurrentUser,
    authorization_context: CurrentAuthContext,
    session: CurrentSession,
):
    """
    Generate a new API key for the current user.
    Replaces any existing API key.
    """
    try:
        return await APIKeyService.for_user(session, authorization_context).generate_api_key(current_user)
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="You are not allowed to generate an API key for this user")


@me_router.delete("/api-key", response_model=Status)
@limiter.limit("5/minute")
async def revoke_api_key(
    request: Request,
    current_user: CurrentUser,
    authorization_context: CurrentAuthContext,
    session: CurrentSession,
):
    """
    Revoke the current user's API key.
    """
    try:
        await APIKeyService.for_user(session, authorization_context).revoke_api_key(current_user)
    except APIKeyNotFoundException as e:
        raise APIKeyNotFoundHTTPException from e
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail="You are not allowed to revoke this API key") from e

    return Status(detail="API key revoked successfully")
