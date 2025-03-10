from uuid import uuid4

import pytest


async def test_validate_bulk_delete_default(service, user_1):
    """
    Test that default _validate_bulk_delete implementation returns True.
    """
    # Arrange
    test_ids = [uuid4(), uuid4()]

    # Act & Assert
    result = await service._validate_bulk_delete(test_ids, user_1)
    assert result is True


async def test_validate_bulk_delete_custom(service, user_1):
    """
    Test custom validation logic in _validate_bulk_delete.
    """
    # Arrange
    validation_called = False
    test_ids = [uuid4(), uuid4()]

    async def custom_validate(ids, user):
        nonlocal validation_called
        validation_called = True
        assert len(ids) == 2  # Vérifie que tous les IDs sont passés
        assert user.id == user_1.id  # Vérifie que l'utilisateur est correct
        if len(ids) > 5:
            raise ValueError("Cannot delete more than 5 items at once")
        return True

    service._validate_bulk_delete = custom_validate

    # Act
    await service._validate_bulk_delete(test_ids, user_1)

    # Assert
    assert validation_called, "Custom validation should have been called"


async def test_validate_bulk_delete_custom_failure(service, user_1):
    """
    Test that _validate_bulk_delete can properly raise exceptions.
    """
    # Arrange
    test_ids = [uuid4() for _ in range(6)]  # Create 6 IDs

    async def custom_validate(ids, user):
        if len(ids) > 5:
            raise ValueError("Cannot delete more than 5 items at once")
        return True

    service._validate_bulk_delete = custom_validate

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot delete more than 5 items at once"):
        await service._validate_bulk_delete(test_ids, user_1)
