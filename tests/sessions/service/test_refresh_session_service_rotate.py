from datetime import UTC, datetime, timedelta

import pytest

from app.domains.sessions.exceptions import InvalidRefreshTokenError, RefreshTokenReuseError
from app.domains.sessions.service import RefreshSessionService, hash_refresh_token
from app.domains.users.factory import UserFactory


def _future() -> datetime:
    return datetime.now(UTC) + timedelta(days=7)


@pytest.mark.anyio
async def test_rotate_marks_old_used_and_issues_successor(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_system(db_session)
    original = await service.issue(user.id, "old", _future())

    # Act
    new = await service.rotate(user.id, "old", "new", _future())

    # Assert - successor in same family, old marked used
    assert new.family_id == original.family_id
    assert new.token_hash == hash_refresh_token("new")
    assert original.used_at is not None


@pytest.mark.anyio
async def test_rotate_unknown_token_raises_invalid(db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_system(db_session)

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate(user.id, "unknown", "new", _future())


@pytest.mark.anyio
async def test_rotate_wrong_user_raises_invalid(db_session):
    # Arrange - token belongs to another user
    owner = await UserFactory.create_async(session=db_session)
    attacker = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_system(db_session)
    await service.issue(owner.id, "old", _future())

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate(attacker.id, "old", "new", _future())


@pytest.mark.anyio
async def test_rotate_expired_token_raises_invalid(db_session):
    # Arrange - already-expired session
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_system(db_session)
    await service.issue(user.id, "old", datetime.now(UTC) - timedelta(seconds=1))

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate(user.id, "old", "new", _future())


@pytest.mark.anyio
async def test_rotate_reused_token_raises_and_revokes_family(db_session):
    # Arrange - rotate once so the original token is consumed
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_system(db_session)
    await service.issue(user.id, "R1", _future())
    await service.rotate(user.id, "R1", "R2", _future())

    # Act / Assert - replaying the consumed R1 is detected as reuse
    with pytest.raises(RefreshTokenReuseError):
        await service.rotate(user.id, "R1", "R3", _future())

    # And the whole family is revoked: the live R2 can no longer be rotated
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate(user.id, "R2", "R4", _future())


@pytest.mark.anyio
async def test_rotate_revoked_token_raises_invalid(db_session):
    # Arrange - issue then revoke
    user = await UserFactory.create_async(session=db_session)
    service = RefreshSessionService.for_system(db_session)
    await service.issue(user.id, "tok", _future())
    await service.revoke("tok")

    # Act / Assert
    with pytest.raises(InvalidRefreshTokenError):
        await service.rotate(user.id, "tok", "new", _future())
