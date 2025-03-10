import pytest

from tests.core.conftest import CreateModelSchema


async def test_bulk_create_success(service, auth_context_user_1):
    """
    Test successful bulk creation of entities with valid data.
    """
    # Arrange
    test_data = [CreateModelSchema(name=f"Bulk Entity {i}") for i in range(3)]

    # Act
    created_entities = await service.bulk_create(test_data, auth_context_user_1)

    # Assert
    assert len(created_entities) == 3
    for i, entity in enumerate(created_entities):
        assert entity.name == f"Bulk Entity {i}"
        assert entity.created_by == auth_context_user_1.user_email
        assert entity.updated_by == auth_context_user_1.user_email


async def test_bulk_create_empty_list(service, auth_context_user_1):
    """
    Test bulk creation with empty list returns empty list.
    """
    # Act
    created_entities = await service.bulk_create([], auth_context_user_1)

    # Assert
    assert isinstance(created_entities, list)
    assert len(created_entities) == 0


async def test_bulk_create_with_custom_validation(service, auth_context_user_1):
    """
    Test bulk create with custom validation logic.
    """
    validated_items = []

    # Override validation method
    async def custom_validate(items: list[dict], user):
        nonlocal validated_items
        validated_items.extend(items)
        for item in items:
            assert "name" in item
            assert item["created_by"] == user.user_email
        return True

    service._validate_bulk_create = custom_validate

    # Arrange
    test_data = [CreateModelSchema(name=f"Validation Entity {i}") for i in range(2)]

    # Act
    created_entities = await service.bulk_create(test_data, auth_context_user_1)

    # Assert
    assert len(validated_items) == 2
    assert len(created_entities) == 2
    assert all(
        item["created_by"] == auth_context_user_1.user_email for item in validated_items
    )


async def test_bulk_create_with_failed_validation(service, auth_context_user_1):
    """
    Test bulk create when validation fails.
    """

    # Override validation method to always fail
    async def validation_fail(*args, **kwargs):
        raise ValueError("Bulk validation failed")

    service._validate_bulk_create = validation_fail

    # Arrange
    test_data = [CreateModelSchema(name=f"Should Fail {i}") for i in range(2)]

    # Act & Assert
    with pytest.raises(ValueError, match="Bulk validation failed"):
        await service.bulk_create(test_data, auth_context_user_1)


async def test_bulk_create_prepares_each_item(service, auth_context_user_1):
    """
    Test that bulk create correctly prepares each item before saving.
    """
    prepared_items = []

    # Override prepare method to track prepared items
    def custom_prepare(data, user):
        prepared_data = {
            "name": f"{data.name}_prepared",
            "created_by": user.user_email,
            "updated_by": user.user_email,
        }
        prepared_items.append(prepared_data)
        return prepared_data

    service._prepare_bulk_create_data = custom_prepare

    # Arrange
    test_data = [CreateModelSchema(name=f"Prep Entity {i}") for i in range(2)]

    # Act
    created_entities = await service.bulk_create(
        test_data, authorization_context=auth_context_user_1
    )

    # Assert
    assert len(prepared_items) == 2
    assert len(created_entities) == 2
    for i, entity in enumerate(created_entities):
        assert entity.name == f"Prep Entity {i}_prepared"
        assert entity.created_by == auth_context_user_1.user_email
