import uuid


async def test_get_by_id_success(repository, populated_db, auth_context_user_1):
    """Test retrieval of an entity by ID"""
    # Arrange
    item_to_retrieve = populated_db[0]

    # Act
    result = await repository.get_by_id(
        id=str(item_to_retrieve.id),
        authorization_context=auth_context_user_1,
    )

    # Assert
    assert result is not None
    assert result.id == item_to_retrieve.id


async def test_get_by_id_not_found(repository, auth_context_user_1):
    """Test get_by_id with a non-existent ID"""
    # Arrange
    non_existent_id = str(uuid.uuid4())

    # Act
    result = await repository.get_by_id(
        id=non_existent_id, authorization_context=auth_context_user_1
    )

    # Assert
    assert result is None
