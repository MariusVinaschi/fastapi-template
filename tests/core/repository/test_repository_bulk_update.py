import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


@pytest.mark.anyio
async def test_bulk_update_success(repository, populated_db):
    """Test successful bulk update of entities"""
    # Arrange
    instances = populated_db[:2]
    data = {"name": "Updated Name"}

    # Act
    updated_instances = await repository.bulk_update(instances, data)

    # Assert
    assert len(updated_instances) == 2
    for updated in updated_instances:
        assert updated.name == data["name"]


@pytest.mark.anyio
async def test_bulk_update_verify_in_db(repository, db_session, populated_db):
    """Test that bulk updated entities are actually persisted in database"""
    # Arrange
    instances = populated_db[:2]
    data = {"name": "DB Verified"}

    # Act
    updated_instances = await repository.bulk_update(instances, data)

    # Verify in DB
    ids = [instance.id for instance in updated_instances]
    query = select(repository.model).where(repository.model.id.in_(ids))
    result = await db_session.scalars(query)
    db_instances = result.all()

    # Assert
    assert len(db_instances) == 2
    for db_instance in db_instances:
        assert db_instance.name == data["name"]


@pytest.mark.anyio
async def test_bulk_update_empty_lists(repository):
    """Test bulk update with empty lists"""
    # Arrange
    empty_instances = []
    data = {"name": "Won't be used"}

    # Act
    result = await repository.bulk_update(empty_instances, data)

    # Assert
    assert result == []


@pytest.mark.anyio
async def test_bulk_update_partial(repository, populated_db):
    """Test partial bulk update (only updating name field)"""
    # Arrange
    instances = populated_db[:2]
    data = {"name": "Partial Update"}

    # Act
    updated_instances = await repository.bulk_update(instances, data)

    # Assert
    for updated in updated_instances:
        assert updated.name == data["name"]


@pytest.mark.anyio
async def test_bulk_update_preserves_created_at(repository, populated_db):
    """Test that bulk update doesn't modify created_at timestamps"""
    # Arrange
    instances = populated_db[:2]
    original_created_ats = [instance.created_at for instance in instances]
    data = {"name": "New Name"}

    # Act
    updated_instances = await repository.bulk_update(instances, data)

    # Assert
    for updated, original_created_at in zip(updated_instances, original_created_ats):
        assert updated.created_at == original_created_at
        assert updated.name == data["name"]


@pytest.mark.anyio
async def test_bulk_update_with_null_required_field(repository, populated_db):
    """Test bulk update with NULL value for required field"""
    # Arrange
    instances = populated_db[:2]
    data = {"name": None}  # Required field

    # Act & Assert
    with pytest.raises(IntegrityError):
        await repository.bulk_update(instances, data)
