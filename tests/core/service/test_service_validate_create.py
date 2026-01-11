
from tests.core.conftest import CreateModelSchema


async def test_validate_create(service, user_1):
    """
    Test that _validate_create correctly validates data for entity creation
    """
    # Arrange
    test_data = CreateModelSchema(name="Test Entity")

    # Act
    result = await service._validate_create(test_data, user_1)

    # Assert
    assert result is True
