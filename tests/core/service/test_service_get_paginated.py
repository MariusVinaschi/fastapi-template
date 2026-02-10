import pytest
from app.domains.base.filters import BaseFilterParams
from tests.core.conftest import CreateModelSchema


@pytest.mark.anyio
async def test_get_paginated_basic(service_factory, populated_db, auth_context_user_1):
    """Test basic pagination functionality of the service"""
    # Arrange
    service = service_factory(auth_context_user_1)
    filters = BaseFilterParams(offset=0, limit=10)

    # Act
    result = await service.get_paginated(filters)

    # Assert
    assert result["count"] == len(populated_db)
    assert len(result["data"]) == len(populated_db)


@pytest.mark.anyio
async def test_get_paginated_with_search(service_factory, populated_db, auth_context_user_1):
    """Test pagination with search functionality"""
    # Arrange
    service = service_factory(auth_context_user_1)
    items = [
        CreateModelSchema(
            name="Searchable Item",
        ),
        CreateModelSchema(
            name="Another Search Term",
        ),
        CreateModelSchema(name="No Match"),
    ]
    for item in items:
        await service.create(item)

    filters = BaseFilterParams(offset=0, limit=10, search="Search")

    # Act
    result = await service.get_paginated(filters)

    # Assert
    assert result["count"] == 2
    assert len(result["data"]) == 2
    assert all("search" in item.name.lower() for item in result["data"])


@pytest.mark.anyio
async def test_get_paginated_with_id_filter(service_factory, populated_db, auth_context_user_1):
    """Test pagination with id__in filter"""
    # Arrange
    service = service_factory(auth_context_user_1)
    # Create test items using the schema
    items = [CreateModelSchema(name=f"Test Item {i}") for i in range(3)]
    created_items = []
    for item in items:
        created = await service.create(item)
        created_items.append(created)

    selected_ids = [str(item.id) for item in created_items[:2]]
    filters = BaseFilterParams(offset=0, limit=10, id__in=selected_ids)

    # Act
    result = await service.get_paginated(filters)

    # Assert
    assert result["count"] == len(selected_ids)
    assert len(result["data"]) == len(selected_ids)
    result_ids = [str(item.id) for item in result["data"]]
    assert all(id in selected_ids for id in result_ids)


@pytest.mark.anyio
async def test_get_paginated_with_offset(service_factory, populated_db, auth_context_user_1):
    """Test pagination with offset"""
    # Arrange
    service = service_factory(auth_context_user_1)
    filters_first = BaseFilterParams(offset=0, limit=2)
    filters_second = BaseFilterParams(offset=2, limit=2)

    # Act
    first_page = await service.get_paginated(filters_first)
    second_page = await service.get_paginated(filters_second)

    # Assert
    assert first_page["count"] == second_page["count"]
    assert len(first_page["data"]) == 2
    assert len(second_page["data"]) == 2
    first_page_ids = [item.id for item in first_page["data"]]
    second_page_ids = [item.id for item in second_page["data"]]
    assert not any(id in first_page_ids for id in second_page_ids)
