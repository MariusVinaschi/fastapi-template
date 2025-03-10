from app.core.filters import BaseFilterParams
from tests.core.conftest import CreateModelSchema


async def test_get_paginated_basic(service, populated_db, auth_context_user_1):
    """Test basic pagination functionality of the service"""
    # Arrange
    filters = BaseFilterParams(offset=0, limit=10)

    # Act
    result = await service.get_paginated(auth_context_user_1, filters)

    # Assert
    assert result["count"] == len(populated_db)
    assert len(result["data"]) == len(populated_db)


async def test_get_paginated_with_search(service, populated_db, auth_context_user_1):
    """Test pagination with search functionality"""
    # Arrange
    items = [
        CreateModelSchema(
            name="Searchable Item",
            created_by="user1@test.com",
            updated_by="user1@test.com",
        ),
        CreateModelSchema(
            name="Another Search Term",
            created_by="user1@test.com",
            updated_by="user1@test.com",
        ),
        CreateModelSchema(
            name="No Match", created_by="user1@test.com", updated_by="user1@test.com"
        ),
    ]
    for item in items:
        await service.create(authorization_context=auth_context_user_1, data=item)

    filters = BaseFilterParams(offset=0, limit=10, search="Search")

    # Act
    result = await service.get_paginated(auth_context_user_1, filters)

    # Assert
    assert result["count"] == 2
    assert len(result["data"]) == 2
    assert all("search" in item.name.lower() for item in result["data"])


async def test_get_paginated_with_id_filter(service, populated_db, auth_context_user_1):
    """Test pagination with id__in filter"""
    # Arrange
    # Create test items using the schema
    items = [CreateModelSchema(name=f"Test Item {i}") for i in range(3)]
    created_items = []
    for item in items:
        created = await service.create(
            authorization_context=auth_context_user_1, data=item
        )
        created_items.append(created)

    selected_ids = [str(item.id) for item in created_items[:2]]
    filters = BaseFilterParams(offset=0, limit=10, id__in=selected_ids)

    # Act
    result = await service.get_paginated(auth_context_user_1, filters)

    # Assert
    assert result["count"] == len(selected_ids)
    assert len(result["data"]) == len(selected_ids)
    result_ids = [str(item.id) for item in result["data"]]
    assert all(id in selected_ids for id in result_ids)


async def test_get_paginated_with_offset(service, populated_db, auth_context_user_1):
    """Test pagination with offset"""
    # Arrange
    filters_first = BaseFilterParams(offset=0, limit=2)
    filters_second = BaseFilterParams(offset=2, limit=2)

    # Act
    first_page = await service.get_paginated(auth_context_user_1, filters_first)
    second_page = await service.get_paginated(auth_context_user_1, filters_second)

    # Assert
    assert first_page["count"] == second_page["count"]
    assert len(first_page["data"]) == 2
    assert len(second_page["data"]) == 2
    first_page_ids = [item.id for item in first_page["data"]]
    second_page_ids = [item.id for item in second_page["data"]]
    assert not any(id in first_page_ids for id in second_page_ids)
