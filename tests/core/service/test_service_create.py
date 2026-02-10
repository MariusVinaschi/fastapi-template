import pytest

from tests.core.conftest import CreateModelSchema


@pytest.mark.anyio
async def test_create_success(service_factory, auth_context_user_1):
    """
    Test successful creation of an entity with valid data.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_data = CreateModelSchema(
        name="New Test Entity",
    )

    # Act
    created_entity = await service.create(test_data)

    # Assert
    assert created_entity is not None
    assert created_entity.name == test_data.name
    assert created_entity.created_by == auth_context_user_1.user_email
    assert created_entity.updated_by == auth_context_user_1.user_email


@pytest.mark.anyio
async def test_create_with_custom_validation(service_factory, auth_context_user_1):
    """
    Test create with custom validation logic.
    """
    validation_called = False
    service = service_factory(auth_context_user_1)

    # Override validation method
    async def custom_validate(data: dict):
        nonlocal validation_called
        validation_called = True
        assert data["name"] == "Custom Validation Test"
        return True

    service._validate_create = custom_validate

    # Arrange
    test_data = CreateModelSchema(name="Custom Validation Test")

    # Act
    created_entity = await service.create(test_data)

    # Assert
    assert validation_called, "Custom validation was not called"
    assert created_entity is not None
    assert created_entity.name == test_data.name


@pytest.mark.anyio
async def test_create_with_failed_validation(service_factory, auth_context_user_1):
    """
    Test create when validation fails.
    """

    # Arrange
    service = service_factory(auth_context_user_1)

    # Override validation method to always fail
    async def validation_fail(*args, **kwargs):
        raise ValueError("Validation failed")

    service._validate_create = validation_fail

    # Arrange
    test_data = CreateModelSchema(name="Should Fail")

    # Act & Assert
    with pytest.raises(ValueError, match="Validation failed"):
        await service.create(test_data)


@pytest.mark.anyio
async def test_create_prepares_data_correctly(service_factory, auth_context_user_1):
    """
    Test that create method correctly prepares data before saving.
    """
    prepare_called = False
    service = service_factory(auth_context_user_1)

    # Override prepare method to verify it's called with correct data
    def custom_prepare(data):
        nonlocal prepare_called
        prepare_called = True
        prepared_data = {
            "name": f"{data.name}_prepared",  # Slightly change name to confirm preparation ran
            "created_by": service.authorization_context.user_email,
            "updated_by": service.authorization_context.user_email,
        }
        return prepared_data

    service._prepare_create_data = custom_prepare

    # Arrange
    test_data = CreateModelSchema(
        name="Test Preparation",
    )

    # Act
    created_entity = await service.create(test_data)

    # Assert
    assert prepare_called, "Data preparation method was not called"
    assert created_entity is not None
    assert created_entity.name == f"{test_data.name}_prepared"
    assert created_entity.created_by == auth_context_user_1.user_email
    assert created_entity.updated_by == auth_context_user_1.user_email
