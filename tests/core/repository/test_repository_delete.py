import pytest
from sqlalchemy import func, select


@pytest.mark.anyio
async def test_delete_success(repository, populated_db):
    """Test successful deletion of an entity"""
    # Arrange
    instance = populated_db[0]
    instance_id = instance.id

    # Act
    result = await repository.delete(instance)

    # Assert
    assert result is True

    # Verify the instance is no longer in DB
    query = select(repository.model).where(repository.model.id == instance_id)
    result = await repository.session.scalars(query)
    assert result.one_or_none() is None


@pytest.mark.anyio
async def test_delete_verify_other_instances_remain(repository, populated_db):
    """Test that deleting one instance doesn't affect others"""
    # Arrange
    instance_to_delete = populated_db[0]
    remaining_instance = populated_db[1]

    # Act
    await repository.delete(instance_to_delete)

    # Assert remaining instance still exists
    query = select(repository.model).where(repository.model.id == remaining_instance.id)
    result = await repository.session.scalars(query)
    db_instance = result.one_or_none()
    assert db_instance is not None
    assert db_instance.id == remaining_instance.id


@pytest.mark.anyio
async def test_delete_and_commit_rollback(repository, populated_db, db_session):
    """Test deletion with transaction rollback on error"""
    # Arrange
    instance = populated_db[0]
    instance_id = instance.id

    # Simulate an error after delete
    async def failing_commit():
        raise Exception("Simulated error")

    # Replace _commit with failing version
    original_commit = repository._commit
    repository._commit = failing_commit

    # Act & Assert
    with pytest.raises(Exception):
        await repository.delete(instance)

    # Restore original commit
    repository._commit = original_commit

    # Verify instance still exists due to rollback
    query = select(repository.model).where(repository.model.id == instance_id)
    result = await db_session.scalars(query)
    assert result.one_or_none() is not None


@pytest.mark.anyio
async def test_delete_invalid_instance(repository):
    """Test deleting an instance that was never persisted"""
    # Arrange
    invalid_instance = repository.model(name="Never Persisted")

    # Act & Assert
    with pytest.raises(Exception):
        await repository.delete(invalid_instance)


@pytest.mark.anyio
async def test_delete_all_instances(repository, populated_db):
    """Test deleting all instances sequentially"""
    # Act
    for instance in populated_db:
        await repository.delete(instance)

    # Assert
    query = select(func.count()).select_from(repository.model)
    result = await repository.session.scalar(query)
    assert result == 0
