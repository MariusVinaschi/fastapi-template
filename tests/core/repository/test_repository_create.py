from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError


async def test_create_success(repository, sample_data):
    """Test successful creation of a single entity"""
    # Arrange
    data = sample_data[0]

    # Act
    instance = await repository.create(data)

    # Assert
    assert instance is not None
    assert isinstance(instance.id, UUID)
    assert instance.name == data["name"]
    assert instance.created_by == data["created_by"]
    assert instance.updated_by == data["updated_by"]


async def test_create_with_missing_required_field(repository):
    """Test creation with missing required field"""
    # Arrange
    incomplete_data = {
        "name": "Test 1"
        # organization_id manquant
    }

    # Act & Assert
    with pytest.raises(IntegrityError):
        await repository.create(incomplete_data)


async def test_create_verify_in_db(repository, db_session, sample_data):
    """Test that created entity is actually persisted in database"""
    # Arrange
    data = sample_data[0]

    # Act
    instance = await repository.create(data)

    # Verify in DB
    from sqlalchemy import select

    query = select(repository.model).where(repository.model.id == instance.id)
    result = await db_session.execute(query)
    db_instance = result.scalar_one()

    # Assert
    assert db_instance is not None
    assert isinstance(db_instance.id, UUID)
    assert db_instance.name == data["name"]
    assert db_instance.created_by == data["created_by"]
    assert db_instance.updated_by == data["updated_by"]


async def test_create_with_extra_field(repository):
    """Test creation with extra field that doesn't exist in model"""
    # Arrange
    data_with_extra = {
        "name": "Test Extra",
        "non_existent_field": "this field doesn't exist",
    }

    # Act & Assert
    with pytest.raises(TypeError):
        await repository.create(data_with_extra)
