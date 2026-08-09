from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domains.sessions.service import RefreshSessionService, hash_refresh_token
from app.domains.users.authorization import UserAuthorizationAdapter
from app.domains.users.factory import UserFactory


@pytest.mark.anyio
async def test_issue_persists_hashed_token_and_new_family(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_user(db_session, UserAuthorizationAdapter(user))
    expires_at = datetime.now(UTC) + timedelta(days=7)

    # Act
    created = await service.issue(user.id, "refresh-token", expires_at)

    # Assert - the raw token is never stored, only its hash
    assert created.user_id == user.id
    assert created.token_hash == hash_refresh_token("refresh-token")
    assert created.family_id is not None
    assert created.used_at is None
    assert created.revoked_at is None


@pytest.mark.anyio
async def test_issue_reuses_supplied_family_id(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_user(db_session, UserAuthorizationAdapter(user))
    expires_at = datetime.now(UTC) + timedelta(days=7)
    family_id = uuid4()

    # Act
    created = await service.issue(user.id, "refresh-token", expires_at, family_id=family_id)

    # Assert
    assert created.family_id == family_id
