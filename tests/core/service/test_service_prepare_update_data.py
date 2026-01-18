from tests.core.conftest import UpdateModelSchema


async def test_prepare_update_data(service_factory, auth_context_user_1):
    """
    Test that _prepare_update_data correctly prepares data for entity update.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_data = UpdateModelSchema(name="Updated Name")

    # Act
    prepared_data = service._prepare_update_data(test_data)

    # Assert
    assert prepared_data["name"] == test_data.name
    assert prepared_data["updated_by"] == auth_context_user_1.user_email
    # Check that only necessary fields are included
    assert set(prepared_data.keys()) == {"name", "updated_by"}


async def test_prepare_update_data_partial(service_factory, auth_context_user_1):
    """
    Test that _prepare_update_data correctly handles partial updates.
    """
    # Arrange
    service = service_factory(auth_context_user_1)
    test_data = UpdateModelSchema(name="Updated Name")  # Only name is provided

    # Act
    prepared_data = service._prepare_update_data(test_data)

    # Assert
    assert prepared_data["name"] == test_data.name
    assert "updated_by" in prepared_data
    assert prepared_data["updated_by"] == auth_context_user_1.user_email
