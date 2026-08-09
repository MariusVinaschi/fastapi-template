from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domains.sessions.factory import RefreshSessionFactory
from app.domains.sessions.repository import RefreshSessionRepository
from app.domains.users.factory import UserFactory


@pytest.mark.anyio
async def test_revoke_family_revokes_all_active_tokens(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    family_id = uuid4()
    first = await RefreshSessionFactory.create_async(
        session=db_session, user=user, family_id=family_id, token_hash="h1"
    )
    second = await RefreshSessionFactory.create_async(
        session=db_session, user=user, family_id=family_id, token_hash="h2"
    )
    repository = RefreshSessionRepository(db_session)

    # Act
    revoked_count = await repository.revoke_family(family_id)

    # Assert
    assert revoked_count == 2
    assert first.revoked_at is not None
    assert second.revoked_at is not None


@pytest.mark.anyio
async def test_revoke_family_ignores_already_revoked_tokens(db_session):
    # Arrange - one already revoked, one active, same family
    family_id = uuid4()
    await RefreshSessionFactory.create_async(
        session=db_session, family_id=family_id, token_hash="revoked", revoked_at=datetime.now(UTC)
    )
    await RefreshSessionFactory.create_async(session=db_session, family_id=family_id, token_hash="active")
    repository = RefreshSessionRepository(db_session)

    # Act
    revoked_count = await repository.revoke_family(family_id)

    # Assert - only the active token is counted
    assert revoked_count == 1


@pytest.mark.anyio
async def test_revoke_family_only_affects_target_family(db_session):
    # Arrange - two distinct families
    target_family = uuid4()
    other_family = uuid4()
    await RefreshSessionFactory.create_async(session=db_session, family_id=target_family, token_hash="target")
    await RefreshSessionFactory.create_async(session=db_session, family_id=other_family, token_hash="other")
    repository = RefreshSessionRepository(db_session)

    # Act
    await repository.revoke_family(target_family)

    # Assert - the other family is untouched
    survivor = await repository.find_by_hash("other")
    assert survivor is not None
    assert survivor.revoked_at is None
