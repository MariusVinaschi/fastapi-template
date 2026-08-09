from datetime import UTC, datetime, timedelta

import pytest

from app.domains.sessions.service import RefreshSessionService
from app.domains.users.authorization import UserAuthorizationAdapter
from app.domains.users.factory import UserFactory


@pytest.mark.anyio
async def test_revoke_revokes_family_and_returns_count(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_user(db_session, UserAuthorizationAdapter(user))
    issued = await service.issue(user.id, "tok", datetime.now(UTC) + timedelta(days=7))

    # Act
    count = await service.revoke("tok")

    # Assert
    assert count == 1
    assert issued.revoked_at is not None


@pytest.mark.anyio
async def test_revoke_unknown_token_returns_zero(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_user(db_session, UserAuthorizationAdapter(user))

    # Act / Assert
    assert await service.revoke("unknown") == 0
