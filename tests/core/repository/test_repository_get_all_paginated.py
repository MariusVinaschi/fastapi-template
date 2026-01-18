from app.domains.base.filters import BaseFilterParams


async def test_get_paginated_basic(repository, populated_db):
    """Test basic pagination functionality"""
    # Arrange
    filters = BaseFilterParams(offset=0, limit=1)

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    expected_count = sum(1 for item in populated_db)
    assert total_count == expected_count
    assert len(results) == 1
    assert isinstance(results[0], repository.model)


async def test_get_paginated_empty_results(repository):
    """Test pagination with empty database"""
    # Arrange
    filters = BaseFilterParams(offset=0, limit=10)

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count == 0
    assert len(results) == 0


async def test_get_paginated_with_ordering(
    repository, populated_db
):
    """Test pagination with ordering"""
    # Arrange
    filters = BaseFilterParams(offset=0, limit=10, order_by="name")

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count > 0
    names = [result.name for result in results]
    assert names == sorted(names)


async def test_get_paginated_with_ordering_desc(
    repository, populated_db
):
    """Test pagination with descending ordering"""
    # Arrange
    filters = BaseFilterParams(offset=0, limit=10, order_by="-name")

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count > 0
    names = [result.name for result in results]
    assert names == sorted(names, reverse=True)


async def test_get_paginated_different_pages(
    repository, populated_db
):
    """Test accessing different pages with pagination"""
    # Arrange
    additional_data = [
        {
            "name": f"Extra Item {i}",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        }
        for i in range(3)
    ]
    await repository.bulk_create(additional_data)

    page_size = 1

    # First page
    filters_page1 = BaseFilterParams(offset=0, limit=page_size)
    # Second page
    filters_page2 = BaseFilterParams(offset=page_size, limit=page_size)

    # Act
    total_count1, page1_results = await repository.get_paginated(
        filters=filters_page1
    )
    total_count2, page2_results = await repository.get_paginated(
        filters=filters_page2
    )

    # Assert
    assert total_count1 == total_count2  # Total count should be consistent
    assert len(page1_results) == page_size
    assert len(page2_results) == page_size
    assert (
        page1_results[0].id != page2_results[0].id
    )  # Different items on different pages


async def test_get_paginated_offset_exceeds_total(
    repository, populated_db
):
    """Test pagination with offset exceeding total count"""
    # Arrange
    filters = BaseFilterParams(offset=1000, limit=10)

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    expected_count = sum(1 for item in populated_db)
    assert total_count == expected_count
    assert len(results) == 0


async def test_get_paginated_with_search(repository, populated_db):
    """Test pagination with search filter"""
    # Arrange
    search_data = [
        {
            "name": "Searchable Item",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
        {
            "name": "Another Search Item",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
        {
            "name": "Different Item",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
    ]
    await repository.bulk_create(search_data)
    filters = BaseFilterParams(offset=0, limit=10, search="Search")

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count == 2
    assert len(results) == 2
    for result in results:
        assert "search" in result.name.lower()


async def test_get_paginated_with_search_no_results(
    repository, populated_db
):
    """Test pagination with search filter that matches nothing"""
    # Arrange
    filters = BaseFilterParams(offset=0, limit=10, search="NonExistentTerm123")

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count == 0
    assert len(results) == 0


async def test_get_paginated_with_case_insensitive_search(
    repository, populated_db
):
    """Test that search is case insensitive"""
    # Arrange
    test_name = "UniqueSearchTerm"
    await repository.create(
        {
            "name": test_name.upper(),
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        }
    )

    filters = BaseFilterParams(offset=0, limit=10, search=test_name.lower())

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count == 1
    assert len(results) == 1
    assert results[0].name == test_name.upper()


async def test_get_paginated_with_id_in_filter(
    repository, populated_db
):
    """Test pagination with id__in filter"""
    # Arrange
    org_1_items = [item for item in populated_db]
    selected_ids = [str(item.id) for item in org_1_items[:2]]  # Take first two items

    filters = BaseFilterParams(offset=0, limit=10, id__in=selected_ids)

    # Act
    total_count, results = await repository.get_paginated(
        filters=filters
    )

    # Assert
    assert total_count == len(selected_ids)
    assert len(results) == len(selected_ids)
    result_ids = [str(result.id) for result in results]
    assert all(id in selected_ids for id in result_ids)
