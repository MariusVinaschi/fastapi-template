from uuid import uuid4

import pytest


async def test_bulk_delete_success(service, populated_db, auth_context_user_1):
    """
    Test successful bulk deletion with validation.
    """
    # Arrange
    validation_called = False
    instance_ids = [str(instance.id) for instance in populated_db[:2]]

    async def custom_validate(ids, user):
        nonlocal validation_called
        validation_called = True
        return True

    service._validate_bulk_delete = custom_validate

    # Act
    deleted_count = await service.bulk_delete(instance_ids, auth_context_user_1)

    # Assert
    assert validation_called, "Validation should have been called"
    assert deleted_count == 2, "Should have deleted exactly 2 records"

    # Verify entities are actually deleted
    for instance_id in instance_ids:
        result = await service.repository.get_by_id(instance_id, auth_context_user_1)
        assert result is None


async def test_bulk_delete_empty_list(service, populated_db, auth_context_user_1):
    """
    Test bulk delete with empty list.
    """
    # Arrange
    validation_called = False

    async def custom_validate(ids, user):
        nonlocal validation_called
        validation_called = True
        return True

    service._validate_bulk_delete = custom_validate

    # Act
    deleted_count = await service.bulk_delete([], auth_context_user_1)

    # Assert
    assert validation_called, "Validation should be called even with empty list"
    assert deleted_count == 0, "Should return 0 for empty list"


async def test_bulk_delete_validation_failure_prevents_deletion(
    service, populated_db, auth_context_user_1
):
    """
    Test that validation failure prevents deletion of any entities.
    """
    # Arrange
    instance_ids = [str(instance.id) for instance in populated_db[:2]]

    async def validation_fail(ids, user):
        raise ValueError("Bulk delete not allowed")

    service._validate_bulk_delete = validation_fail

    # Act & Assert
    with pytest.raises(ValueError, match="Bulk delete not allowed"):
        await service.bulk_delete(instance_ids, auth_context_user_1)

    # Verify no entities were deleted
    for instance_id in instance_ids:
        result = await service.repository.get_by_id(instance_id, auth_context_user_1)
        assert result is not None


async def test_bulk_delete_partial_existence(
    service, populated_db, auth_context_user_1
):
    """
    Test bulk delete with mix of existing and non-existent IDs.
    """
    # Arrange
    instance_ids = [str(populated_db[0].id), str(uuid4())]

    # Act
    deleted_count = await service.bulk_delete(instance_ids, auth_context_user_1)

    # Assert
    assert deleted_count == 1, "Should only delete the one existing record"

    # Verify the existing entity was deleted
    result = await service.repository.get_by_id(instance_ids[0], auth_context_user_1)
    assert result is None


async def test_bulk_delete_all_non_existent(service, populated_db, auth_context_user_1):
    """
    Test bulk delete with only non-existent IDs.
    """
    # Arrange
    non_existent_ids = [str(uuid4()) for _ in range(3)]

    # Act
    deleted_count = await service.bulk_delete(non_existent_ids, auth_context_user_1)

    # Assert
    assert deleted_count == 0, "Should return 0 when no records found to delete"
