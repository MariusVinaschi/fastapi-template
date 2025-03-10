import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


async def test_update_success(repository, populated_db):
    """Test successful update of an entity"""
    # Arrange
    instance = populated_db[0]
    update_data = {"name": "Updated Name"}

    # Act
    updated_instance = await repository.update(instance, update_data)

    # Assert
    assert updated_instance.id == instance.id
    assert updated_instance.name == "Updated Name"
    assert updated_instance.created_by == "user1@test.com"
    assert updated_instance.updated_by == "user1@test.com"


async def test_update_verify_in_db(repository, db_session, populated_db):
    """Test that updated entity is actually persisted in database"""
    # Arrange
    instance = populated_db[0]
    update_data = {"name": "Verified Update"}

    # Act
    await repository.update(instance, update_data)

    # Verify in DB
    query = select(repository.model).where(repository.model.id == instance.id)
    result = await db_session.execute(query)
    db_instance = result.scalar_one()

    # Assert
    assert db_instance.name == "Verified Update"


async def test_update_partial(repository, populated_db):
    """Test partial update of an entity (only some fields)"""
    # Arrange
    instance = populated_db[0]
    update_data = {"name": "Partial Update"}

    # Act
    updated_instance = await repository.update(instance, update_data)

    # Assert
    assert updated_instance.name == "Partial Update"


async def test_update_with_null_required_field(repository, populated_db):
    """Test update with NULL value for required field"""
    # Arrange
    instance = populated_db[0]
    invalid_data = {"name": None}

    # Act & Assert
    with pytest.raises(IntegrityError):
        await repository.update(instance, invalid_data)


async def test_update_preserves_created_at(repository, populated_db):
    """Test that update doesn't modify created_at timestamp"""
    # Arrange
    instance = populated_db[0]
    original_created_at = instance.created_at
    update_data = {"name": "New Name"}

    # Act
    updated_instance = await repository.update(instance, update_data)

    # Assert
    assert updated_instance.created_at == original_created_at


async def test_update_empty_data(repository, populated_db):
    """Test update with empty data dict"""
    # Arrange
    instance = populated_db[0]
    original_name = instance.name

    # Act
    updated_instance = await repository.update(instance, {})

    # Assert
    assert updated_instance.name == original_name
