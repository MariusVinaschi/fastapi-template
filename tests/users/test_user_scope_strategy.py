import uuid

import pytest_asyncio
from sqlalchemy import select

from app.domains.users.authorization import UserScopeStrategy
from app.domains.users.factory import UserFactory
from app.domains.users.models import User, UserAuthorizationAdapter


@pytest_asyncio.fixture
async def setup_multiple_users(db_session):
    # Create test users
    user1 = await UserFactory.create_async(session=db_session)
    user2 = await UserFactory.create_async(session=db_session)
    await db_session.commit()
    return user1, user2


async def test_apply_scope_filters_by_user_id(db_session, setup_multiple_users):
    user1, user2 = setup_multiple_users

    # Set the context user_id to user1's id
    auth_context = UserAuthorizationAdapter(user1)

    # Create base query
    query = select(User)

    # Apply the scope
    scoped_query = UserScopeStrategy().apply_scope(query, auth_context)

    # Execute the query
    result = await db_session.execute(scoped_query)
    users = result.scalars().all()

    assert len(users) == 2
    assert users[0].id == user1.id
    assert users[1].id == user2.id


async def test_apply_scope_returns_empty_for_nonexistent_user(
    db_session,
):
    # Set a non-existent user ID
    auth_context = UserAuthorizationAdapter(User(id=uuid.uuid4(), email="test@test.com"))

    # Create base query
    query = select(User)

    # Apply the scope
    scoped_query = UserScopeStrategy().apply_scope(query, auth_context)

    # Execute the query
    result = await db_session.execute(scoped_query)
    users = result.scalars().all()

    # Verify that no users are returned
    assert len(users) == 0
