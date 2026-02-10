import uuid

import pytest
from sqlalchemy import func, select


@pytest.mark.anyio
async def test_bulk_delete_success(repository, populated_db):
    """Test successful bulk deletion of entities"""
    # Arrange
    instances = populated_db
    ids = [instance.id for instance in instances]

    # Act
    deleted_count = await repository.bulk_delete(ids)

    # Assert
    assert deleted_count == len(ids)

    # Verify instances are no longer in DB
    query = select(repository.model).where(repository.model.id.in_(ids))
    result = await repository.session.scalars(query)
    assert len(result.all()) == 0


@pytest.mark.anyio
async def test_bulk_delete_empty_list(repository):
    """Test bulk deletion with empty list"""
    # Arrange
    empty_ids = []

    # Act
    deleted_count = await repository.bulk_delete(empty_ids)

    # Assert
    assert deleted_count == 0


@pytest.mark.anyio
async def test_bulk_delete_partial_existing_ids(repository, populated_db):
    """Test bulk deletion with mix of existing and non-existing IDs"""
    # Arrange
    existing_ids = [instance.id for instance in populated_db]
    non_existing_ids = [
        str(uuid.uuid4()),
        str(uuid.uuid4()),
    ]
    all_ids = existing_ids + non_existing_ids

    # Act
    deleted_count = await repository.bulk_delete(all_ids)

    # Assert
    assert deleted_count == len(existing_ids)

    # Verify only existing ids were deleted
    query = select(repository.model).where(repository.model.id.in_(existing_ids))
    result = await repository.session.scalars(query)
    assert len(result.all()) == 0


@pytest.mark.anyio
async def test_bulk_delete_verify_other_instances(repository, populated_db):
    """Test that bulk delete only removes specified instances"""
    # Arrange
    instance_to_keep = populated_db[0]
    instances_to_delete = populated_db[1:]
    ids_to_delete = [instance.id for instance in instances_to_delete]

    # Act
    await repository.bulk_delete(ids_to_delete)

    # Verify remaining instance
    query = select(repository.model).where(repository.model.id == instance_to_keep.id)
    result = await repository.session.scalars(query)
    remaining_instance = result.one_or_none()

    # Assert
    assert remaining_instance is not None
    assert remaining_instance.id == instance_to_keep.id


@pytest.mark.anyio
async def test_bulk_delete_invalid_id_format(repository, populated_db):
    """Test bulk delete with invalid UUID format"""
    # Arrange
    invalid_ids = [
        "not-a-uuid",
        "123e4567",  # UUID incomplet
        "invalid-uuid-format",
    ]

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await repository.bulk_delete(invalid_ids)

    # Verify the specific error is about invalid UUID format
    assert "invalid UUID" in str(exc_info.value)


@pytest.mark.anyio
async def test_bulk_delete_verify_count(repository, populated_db):
    """Test that bulk delete returns correct count"""
    # Arrange
    initial_count = len(populated_db)
    ids_to_delete = [instance.id for instance in populated_db[:2]]  # Delete first 2

    # Act
    deleted_count = await repository.bulk_delete(ids_to_delete)

    # Assert
    assert deleted_count == len(ids_to_delete)

    # Verify remaining count
    query = select(func.count()).select_from(repository.model)
    remaining_count = await repository.session.scalar(query)
    assert remaining_count == initial_count - len(ids_to_delete)


@pytest.mark.anyio
async def test_bulk_delete_duplicate_ids(repository, populated_db):
    """Test bulk delete with duplicate IDs"""
    # Arrange
    ids = [populated_db[0].id, populated_db[0].id]

    # Act
    deleted_count = await repository.bulk_delete(ids)

    # Assert
    assert deleted_count == 1
