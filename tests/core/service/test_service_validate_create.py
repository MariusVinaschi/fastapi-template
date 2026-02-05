from tests.core.conftest import CreateModelSchema


async def test_validate_create(service_factory, auth_context_user_1):
    """
    Test that _validate_create correctly validates data for entity creation
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_data = CreateModelSchema(name="Test Entity")

    # Act
    result = await service._validate_create(test_data.model_dump())

    # Assert
    assert result is True
