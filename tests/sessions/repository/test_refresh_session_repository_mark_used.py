import pytest

from app.domains.sessions.factory import RefreshSessionFactory
from app.domains.sessions.repository import RefreshSessionRepository


@pytest.mark.anyio
async def test_mark_used_stamps_used_at(db_session):
    # Arrange
    session_row = await RefreshSessionFactory.create_async(session=db_session, token_hash="h1")
    assert session_row.used_at is None
    repository = RefreshSessionRepository(db_session)

    # Act
    updated = await repository.mark_used(session_row)

    # Assert
    assert updated.id == session_row.id
    assert updated.used_at is not None
