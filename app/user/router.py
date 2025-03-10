import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import CurrentSession
from app.core.exceptions import PermissionDenied
from app.core.filters import BaseFilterParams
from app.core.schemas import PaginatedSchema, Status
from app.user.dependencies import (
    CurrentAuthContext,
    CurrentManagerAuthContext,
    CurrentUser,
)
from app.user.exceptions import UserNotFoundException, UserNotFoundHTTPException
from app.user.schemas import UserCreate, UserPatch, UserRead
from app.user.service import UserService

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

log = logging.getLogger("uvicorn")


@router.get("", response_model=PaginatedSchema[UserRead])
async def get_users(
    session: CurrentSession,
    authorization_context: CurrentAuthContext,
    filters: Annotated[BaseFilterParams, Query()],
):
    return await UserService(session).get_paginated(
        authorization_context=authorization_context, filters=filters
    )


@router.post("", response_model=UserRead)
async def create_user(
    data: UserCreate,
    authorization_context: CurrentManagerAuthContext,
    session: CurrentSession,
):
    try:
        return await UserService(session).create(data, authorization_context)
    except IntegrityError:
        raise HTTPException(
            status_code=400, detail="An user with this email already exist"
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="You are not allowed to create a user"
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Error during the creation")


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
async def get_user(
    user_id: UUID,
    authorization_context: CurrentAuthContext,
    session: CurrentSession,
):
    try:
        return await UserService(session).get_by_id(user_id, authorization_context)
    except UserNotFoundException:
        raise UserNotFoundHTTPException


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserPatch,
    authorization_context: CurrentManagerAuthContext,
    session: CurrentSession,
):
    try:
        return await UserService(session).update(
            user_id, user_update, authorization_context
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException


@router.delete("/{user_id}", response_model=Status)
async def delete_user(
    user_id: UUID,
    session: CurrentSession,
    authorization_context: CurrentManagerAuthContext,
):
    try:
        await UserService(session).delete(user_id, authorization_context)
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete yourself"
        )

    return Status(detail=f"Deleted user {user_id}")


me_router = APIRouter(
    responses={404: {"description": "Not found"}},
)


@me_router.get("", response_model=UserRead)
async def read_users_me(current_user: CurrentUser):
    return current_user
