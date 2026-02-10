from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


@pytest.mark.anyio
async def test_bulk_create_success(repository, sample_data):
    """Test successful bulk creation of entities"""
    # Act
    instances = await repository.bulk_create(sample_data)

    # Assert
    assert len(instances) == len(sample_data)
    for instance, data in zip(instances, sample_data):
        assert instance is not None
        assert isinstance(instance.id, UUID)
        assert instance.name == data["name"]
        assert instance.created_by == data["created_by"]
        assert instance.updated_by == data["updated_by"]


@pytest.mark.anyio
async def test_bulk_create_empty_list(repository):
    """Test bulk creation with empty list"""
    # Arrange
    empty_data = []

    # Act
    instances = await repository.bulk_create(empty_data)

    # Assert
    assert instances == []


@pytest.mark.anyio
async def test_bulk_create_verify_in_db(repository, db_session, sample_data):
    """Test that bulk created entities are actually persisted in database"""
    # Act
    instances = await repository.bulk_create(sample_data)

    # Verify in DB
    ids = [instance.id for instance in instances]
    query = select(repository.model).where(repository.model.id.in_(ids))
    result = await db_session.scalars(query)
    db_instances = result.all()

    # Assert
    assert len(db_instances) == len(sample_data)
    for instance, data in zip(db_instances, sample_data):
        assert instance.name == data["name"]
        assert instance.created_by == data["created_by"]
        assert instance.updated_by == data["updated_by"]


@pytest.mark.anyio
async def test_bulk_create_with_duplicate_data(repository, populated_db):
    """Test bulk creation with duplicate data"""
    # Arrange
    existing_instance = populated_db[0]
    duplicate_data = [
        {
            "id": existing_instance.id,
            "name": "Duplicate Test",
        }
    ]

    # Act & Assert
    with pytest.raises(IntegrityError):
        await repository.bulk_create(duplicate_data)


@pytest.mark.anyio
async def test_bulk_create_with_invalid_data(repository):
    """Test bulk creation with invalid data"""
    # Arrange
    invalid_data = [
        {
            "name": "Test 1",
            # missing organization_id
        },
        {"name": "Test 2", "organization_id": "org2"},
    ]

    # Act & Assert
    with pytest.raises(IntegrityError):
        await repository.bulk_create(invalid_data)
