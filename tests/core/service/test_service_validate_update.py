import pytest


async def test_validate_update(service_factory, auth_context_user_1):
    """
    Test that _validate_update allows valid updates by default.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    instance = await service.repository.create(
        {
            "name": "Original Name",
            "created_by": "test",
            "updated_by": "test",
        }
    )
    update_data = {"name": "New Name"}

    # Act & Assert - Should not raise any exception
    await service._validate_update(instance, update_data)


async def test_validate_update_custom_validation(service_factory, auth_context_user_1):
    """
    Test that custom validation logic in _validate_update works.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    validation_called = False
    instance = await service.repository.create(
        {
            "name": "Original Name",
            "created_by": "test",
            "updated_by": "test",
        }
    )

    async def custom_validate(inst, data):
        nonlocal validation_called
        validation_called = True
        if data["name"] == "Invalid":
            raise ValueError("Invalid name")
        return True

    service._validate_update = custom_validate

    # Act & Assert - Valid update
    await service._validate_update(instance, {"name": "Valid"})
    assert validation_called

    # Reset flag and test invalid update
    validation_called = False
    with pytest.raises(ValueError, match="Invalid name"):
        await service._validate_update(instance, {"name": "Invalid"})
    assert validation_called
