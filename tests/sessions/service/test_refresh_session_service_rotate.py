from datetime import UTC, datetime, timedelta

import pytest

from app.domains.sessions.exceptions import InvalidRefreshTokenError, RefreshTokenReuseError
from app.domains.sessions.service import RefreshSessionService, hash_refresh_token
from app.domains.users.authorization import UserAuthorizationAdapter
from app.domains.users.factory import UserFactory


def _future() -> datetime:
    return datetime.now(UTC) + timedelta(days=7)


def _service_for(db_session, user):
    return RefreshSessionService.for_user(db_session, UserAuthorizationAdapter(user))


@pytest.mark.anyio
async def test_rotate_marks_old_used_and_issues_successor(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)
    original = await service.issue(user.id, "old", _future())

    # Act
    new = await service.rotate("old", "new", _future())

    # Assert - successor in same family, old marked used
    assert new.family_id == original.family_id
    assert new.token_hash == hash_refresh_token("new")
    assert original.used_at is not None


@pytest.mark.anyio
async def test_rotate_unknown_token_raises_invalid(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate("unknown", "new", _future())


@pytest.mark.anyio
async def test_rotate_other_users_token_reads_as_unknown(db_session):
    # Arrange - token belongs to another user; row scoping hides it from the attacker
    owner = await UserFactory.create_async(session=db_session)
    attacker = await UserFactory.create_async(session=db_session)
    await _service_for(db_session, owner).issue(owner.id, "old", _future())

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await _service_for(db_session, attacker).rotate("old", "new", _future())


@pytest.mark.anyio
async def test_rotate_expired_token_raises_invalid(db_session):
    # Arrange - already-expired session
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)
    await service.issue(user.id, "old", datetime.now(UTC) - timedelta(seconds=1))

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate("old", "new", _future())


@pytest.mark.anyio
async def test_rotate_reused_token_raises_and_revokes_family(db_session):
    # Arrange - rotate once so the original token is consumed
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)
    await service.issue(user.id, "R1", _future())
    await service.rotate("R1", "R2", _future())

    # Act / Assert - replaying the consumed R1 is detected as reuse
    with pytest.raises(RefreshTokenReuseError):
        await service.rotate("R1", "R3", _future())

    # And the whole family is revoked: the live R2 can no longer be rotated
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate("R2", "R4", _future())


@pytest.mark.anyio
async def test_rotate_revoked_token_raises_invalid(db_session):
    # Arrange - issue then revoke
    user = await UserFactory.create_async(session=db_session)
    service = _service_for(db_session, user)
    await service.issue(user.id, "tok", _future())
    await service.revoke("tok")

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate("tok", "new", _future())
