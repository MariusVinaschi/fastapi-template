from uuid import uuid4

import pytest

from app.domains.base.exceptions import EntityNotFoundException


async def test_delete_success(service, populated_db, auth_context_user_1):
    """
    Test successful deletion of an entity.
    """
    # Arrange
    instance = populated_db[0]
    instance_id = instance.id

    # Act
    result = await service.delete(instance_id, auth_context_user_1)

    # Assert
    assert result is True
    # Verify the entity is actually deleted
    with pytest.raises(EntityNotFoundException):
        await service.get_by_id(instance_id, auth_context_user_1)


async def test_delete_non_existent_entity(service, auth_context_user_1):
    """
    Test deletion of non-existent entity.
    """
    # Arrange
    non_existent_id = uuid4()

    # Act & Assert
    with pytest.raises(EntityNotFoundException):
        await service.delete(non_existent_id, auth_context_user_1)
