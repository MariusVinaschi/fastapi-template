import pytest
import uuid


@pytest.mark.anyio
async def test_get_by_id_success(repository, populated_db):
    """Test retrieval of an entity by ID"""
    # Arrange
    item_to_retrieve = populated_db[0]

    # Act
    result = await repository.get_by_id(
        id=str(item_to_retrieve.id),
    )

    # Assert
    assert result is not None
    assert result.id == item_to_retrieve.id


@pytest.mark.anyio
async def test_get_by_id_not_found(repository):
    """Test get_by_id with a non-existent ID"""
    # Arrange
    non_existent_id = str(uuid.uuid4())

    # Act
    result = await repository.get_by_id(id=non_existent_id)

    # Assert
    assert result is None
