from uuid import uuid4

import pytest

from app.domains.base.exceptions import EntityNotFoundException


@pytest.mark.anyio
async def test_get_by_id_success(service_factory, populated_db, auth_context_user_1):
    """Tests successful retrieval of an entity by admin from their organization"""
    # Arrange
    service = service_factory(auth_context_user_1)
    test_entity = populated_db[0]  # First entity from org 1

    # Act
    result = await service.get_by_id(test_entity.id)

    # Assert
    assert result.id == test_entity.id
    assert result.name == test_entity.name


@pytest.mark.anyio
async def test_get_by_id_not_found(service_factory, populated_db, auth_context_user_1):
    """Tests error handling for non-existent entity"""
    # Arrange
    service = service_factory(auth_context_user_1)
    non_existent_id = uuid4()

    # Act & Assert
    with pytest.raises(EntityNotFoundException) as exc_info:
        await service.get_by_id(non_existent_id)

    assert str(exc_info.value) == f"Entity with id {non_existent_id} not found"
