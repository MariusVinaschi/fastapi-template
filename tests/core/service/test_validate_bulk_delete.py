from uuid import uuid4

import pytest


@pytest.mark.anyio
async def test_validate_bulk_delete_default(service_factory, auth_context_user_1):
    """
    Test that default _validate_bulk_delete implementation returns True.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_ids = [uuid4(), uuid4()]

    # Act & Assert
    result = await service._validate_bulk_delete(test_ids)
    assert result is True


@pytest.mark.anyio
async def test_validate_bulk_delete_custom(service_factory, auth_context_user_1):
    """
    Test custom validation logic in _validate_bulk_delete.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    validation_called = False
    test_ids = [uuid4(), uuid4()]

    async def custom_validate(ids):
        nonlocal validation_called
        validation_called = True
        assert len(ids) == 2  # Confirms all IDs are passed
        if len(ids) > 5:
            raise ValueError("Cannot delete more than 5 items at once")
        return True

    service._validate_bulk_delete = custom_validate

    # Act
    await service._validate_bulk_delete(test_ids)

    # Assert
    assert validation_called, "Custom validation should have been called"


@pytest.mark.anyio
async def test_validate_bulk_delete_custom_failure(service_factory, auth_context_user_1):
    """
    Test that _validate_bulk_delete can properly raise exceptions.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_ids = [uuid4() for _ in range(6)]  # Create 6 IDs

    async def custom_validate(ids):
        if len(ids) > 5:
            raise ValueError("Cannot delete more than 5 items at once")
        return True

    service._validate_bulk_delete = custom_validate

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot delete more than 5 items at once"):
        await service._validate_bulk_delete(test_ids)
