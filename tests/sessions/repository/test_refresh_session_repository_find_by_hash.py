import pytest

from app.domains.sessions.factory import RefreshSessionFactory
from app.domains.sessions.repository import RefreshSessionRepository


@pytest.mark.anyio
async def test_find_by_hash_returns_matching_session(db_session):
    # Arrange
    created = await RefreshSessionFactory.create_async(session=db_session, token_hash="known-hash")
    repository = RefreshSessionRepository(db_session)

    # Act
    found = await repository.find_by_hash("known-hash")

    # Assert
    assert found is not None
    assert found.id == created.id


@pytest.mark.anyio
async def test_find_by_hash_returns_none_when_missing(db_session):
    # Arrange
    repository = RefreshSessionRepository(db_session)

    # Act / Assert
    assert await repository.find_by_hash("does-not-exist") is None
