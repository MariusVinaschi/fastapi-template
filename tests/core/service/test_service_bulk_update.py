from uuid import uuid4

import pytest

from app.domains.base.exceptions import EntityNotFoundException
from tests.core.conftest import UpdateModelSchema


async def test_bulk_update_success(service_factory, auth_context_user_1, populated_db):
    """
    Test successful bulk update of entities with valid data.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    instance_ids = [instance.id for instance in populated_db[:2]]
    update_data = UpdateModelSchema(name="Updated Name")

    # Act
    updated_instances = await service.bulk_update(instance_ids, update_data)

    # Assert
    assert len(updated_instances) == len(instance_ids)
    for instance in updated_instances:
        assert instance.name == "Updated Name"
        assert instance.updated_by == auth_context_user_1.user_email


async def test_bulk_update_with_validation(service_factory, auth_context_user_1, populated_db):
    """
    Test bulk update with custom validation logic.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    validation_called = False
    instance_ids = [instance.id for instance in populated_db[:2]]

    async def custom_validate(instances, data):
        nonlocal validation_called
        validation_called = True
        # Custom validation logic - prevent names with "invalid"
        if "invalid" in str(data.get("name", "")).lower():
            raise ValueError("Invalid name detected")
        return True

    service._validate_bulk_update = custom_validate

    # First test - valid update
    valid_update = UpdateModelSchema(name="Valid name")

    # Act - valid update
    updated_instances = await service.bulk_update(instance_ids, valid_update)

    # Assert - valid update
    assert validation_called
    assert len(updated_instances) == len(instance_ids)
    assert all(inst.name == "Valid name" for inst in updated_instances)

    # Reset flag
    validation_called = False

    # Second test - invalid update
    invalid_update = UpdateModelSchema(name="invalid name")

    # Act & Assert - invalid update
    with pytest.raises(ValueError, match="Invalid name detected"):
        await service.bulk_update(instance_ids, invalid_update)

    assert validation_called


async def test_bulk_update_with_missing_entity(service_factory, auth_context_user_1, populated_db):
    """
    Test bulk update with a non-existent entity ID.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    non_existent_id = str(uuid4())
    instance_ids = [populated_db[0].id, non_existent_id]
    update_data = UpdateModelSchema(name="Updated Name")

    # Act & Assert
    with pytest.raises(EntityNotFoundException) as exc_info:
        await service.bulk_update(instance_ids, update_data)

    assert str(non_existent_id) in str(exc_info.value)


async def test_bulk_update_empty_list(service_factory, auth_context_user_1):
    """
    Test bulk update with empty list.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    update_data = UpdateModelSchema(name="Won't be used")

    # Act
    updated_instances = await service.bulk_update([], update_data)

    # Assert
    assert isinstance(updated_instances, list)
    assert len(updated_instances) == 0


async def test_bulk_update_prepare_and_validate_flow(service_factory, auth_context_user_1, populated_db):
    """
    Test the complete bulk update flow including preparation and validation.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    prepare_called = False
    validate_called = False

    instance_ids = [instance.id for instance in populated_db[:2]]

    def custom_prepare(data):
        nonlocal prepare_called
        prepare_called = True
        return {
            "name": f"{data.name}_prepared",
            "updated_by": service.authorization_context.user_email,
        }

    async def custom_validate(instances, data):
        nonlocal validate_called
        validate_called = True
        assert data["name"].endswith("_prepared")
        return True

    service._prepare_bulk_update_data = custom_prepare
    service._validate_bulk_update = custom_validate

    update_data = UpdateModelSchema(name="Bulk Update")

    # Act
    updated_instances = await service.bulk_update(instance_ids, update_data)

    # Assert
    assert prepare_called, "Prepare should be called once"
    assert validate_called, "Validate should be called once"
    assert all(inst.name == "Bulk Update_prepared" for inst in updated_instances)
    assert all(inst.updated_by == auth_context_user_1.user_email for inst in updated_instances)
