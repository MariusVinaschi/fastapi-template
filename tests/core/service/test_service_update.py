from uuid import uuid4

import pytest

from app.domains.base.exceptions import EntityNotFoundException
from tests.core.conftest import UpdateModelSchema


async def test_update_success(service, auth_context_user_1, populated_db):
    """
    Test successful entity update with valid data.
    Instance is from organization_1 where user_1 has access.
    """
    # Arrange
    instance = next(item for item in populated_db)
    update_data = UpdateModelSchema(name="Updated Name")

    # Act
    updated_instance = await service.update(
        instance.id, update_data, auth_context_user_1
    )

    # Assert
    assert updated_instance.id == instance.id  # Same instance
    assert updated_instance.name == "Updated Name"  # Updated field
    assert (
        updated_instance.updated_by == auth_context_user_1.user_email
    )  # Audit field updated


async def test_update_not_found(service, auth_context_user_1):
    """
    Test update with non-existent ID.
    """
    # Arrange
    non_existent_id = uuid4()
    update_data = UpdateModelSchema(name="New Name")

    # Act & Assert
    with pytest.raises(EntityNotFoundException):
        await service.update(non_existent_id, update_data, auth_context_user_1)


async def test_update_validation_failure(service, auth_context_user_1, populated_db):
    """
    Test update with failing validation.
    """
    # Arrange
    instance = next(item for item in populated_db)

    # Override validation to fail
    async def validation_fail(*args, **kwargs):
        raise ValueError("Validation failed")

    service._validate_update = validation_fail
    update_data = UpdateModelSchema(name="Should Fail")

    # Act & Assert
    with pytest.raises(ValueError, match="Validation failed"):
        await service.update(instance.id, update_data, auth_context_user_1)


async def test_update_full_flow(service, auth_context_user_1, populated_db):
    """
    Test the complete update flow with preparation and validation.
    """
    # Arrange
    prepare_called = False
    validate_called = False
    instance = next(item for item in populated_db)

    def custom_prepare(data, user):
        nonlocal prepare_called
        prepare_called = True
        prepared_data = {"name": f"{data.name}_prepared", "updated_by": user.user_email}
        return prepared_data

    async def custom_validate(inst, data, user):
        nonlocal validate_called
        validate_called = True
        assert data["name"].endswith("_prepared")
        return True

    service._prepare_update_data = custom_prepare
    service._validate_update = custom_validate

    update_data = UpdateModelSchema(name="New Name")

    # Act
    updated_instance = await service.update(
        instance.id, update_data, auth_context_user_1
    )

    # Assert
    assert prepare_called, "Prepare method was not called"
    assert validate_called, "Validate method was not called"
    assert updated_instance.name == "New Name_prepared"
    assert updated_instance.updated_by == auth_context_user_1.user_email
