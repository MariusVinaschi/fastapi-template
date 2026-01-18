from tests.core.conftest import CreateModelSchema


async def test_prepare_create_data(service_factory, auth_context_user_1):
    """
    Test that _prepare_create_data correctly prepares data for entity creation
    by adding audit fields (created_by and updated_by).
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_data = CreateModelSchema(name="Test Entity")

    # Act
    prepared_data = service._prepare_create_data(test_data)

    # Assert
    assert prepared_data["name"] == test_data.name
    assert prepared_data["created_by"] == auth_context_user_1.user_email
    assert prepared_data["updated_by"] == auth_context_user_1.user_email
    # Verify no unexpected keys are added
    assert set(prepared_data.keys()) == {
        "name",
        "created_by",
        "updated_by",
    }
