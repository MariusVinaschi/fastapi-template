from uuid import uuid4

import pytest

from app.domains.base.exceptions import EntityNotFoundException


@pytest.mark.asyncio
async def test_get_by_id_success(service, populated_db, auth_context_user_1):
    """Tests successful retrieval of an entity by admin from their organization"""
    # Arrange
    test_entity = populated_db[0]  # First entity from org 1

    # Act
    result = await service.get_by_id(test_entity.id, auth_context_user_1)

    # Assert
    assert result.id == test_entity.id
    assert result.name == test_entity.name


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, populated_db, auth_context_user_1):
    """Tests error handling for non-existent entity"""
    # Arrange
    non_existent_id = uuid4()

    # Act & Assert
    with pytest.raises(EntityNotFoundException) as exc_info:
        await service.get_by_id(non_existent_id, auth_context_user_1)

    assert str(exc_info.value) == f"Entity with id {non_existent_id} not found"
