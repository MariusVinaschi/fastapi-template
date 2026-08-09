from datetime import UTC, datetime, timedelta

import pytest

from app.domains.sessions.service import RefreshSessionService
from app.domains.users.authorization import UserAuthorizationAdapter
from app.domains.users.factory import UserFactory


def _service_for(db_session, user):
    return RefreshSessionService.for_user(db_session, UserAuthorizationAdapter(user))


@pytest.mark.anyio
async def test_find_by_token_returns_owned_session(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)
    issued = await service.issue(user.id, "tok", datetime.now(UTC) + timedelta(days=7))

    # Act
    found = await service.find_by_token("tok")

    # Assert
    assert found is not None
    assert found.id == issued.id


@pytest.mark.anyio
async def test_find_by_token_returns_none_when_missing(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)

    # Act / Assert
    assert await service.find_by_token("unknown") is None


@pytest.mark.anyio
async def test_find_by_token_is_scoped_to_caller(db_session):
    # Arrange - token belongs to another user
    owner = await UserFactory.create_async(session=db_session)
    other = await UserFactory.create_async(session=db_session)
    await _service_for(db_session, owner).issue(owner.id, "tok", datetime.now(UTC) + timedelta(days=7))

    # Act - a different user looks it up
    found = await _service_for(db_session, other).find_by_token("tok")

    # Assert - row scoping hides it
    assert found is None
