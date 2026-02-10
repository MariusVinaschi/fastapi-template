import pytest
from app.domains.base.filters import BaseFilterParams


@pytest.mark.anyio
async def test_get_all_success(repository, populated_db):
    """Test retrieval of all entities"""
    # Arrange
    filters = BaseFilterParams()

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == len(populated_db)
    for result in results:
        assert isinstance(result, repository.model)


@pytest.mark.anyio
async def test_get_all_empty_database(repository):
    """Test get_all with empty database"""
    # Arrange
    filters = BaseFilterParams()

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 0
    assert isinstance(results, list)


@pytest.mark.anyio
async def test_get_all_with_search(repository):
    """Test get_all with search filter"""
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

    filters = BaseFilterParams(search="Search")

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 2
    for result in results:
        assert "search" in result.name.lower()


@pytest.mark.anyio
async def test_get_all_with_ordering_asc(repository, populated_db):
    """Test get_all with ascending ordering"""
    # Arrange
    filters = BaseFilterParams(order_by="name")

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    names = [result.name for result in results]
    assert names == sorted(names)


@pytest.mark.anyio
async def test_get_all_with_ordering_desc(repository, populated_db):
    """Test get_all with descending ordering"""
    # Arrange
    filters = BaseFilterParams(order_by="-name")

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    names = [result.name for result in results]
    assert names == sorted(names, reverse=True)


@pytest.mark.anyio
async def test_get_all_invalid_ordering(repository, populated_db):
    """Test get_all with invalid ordering field"""
    # Arrange
    filters = BaseFilterParams(order_by="non_existent_field")

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) > 0


@pytest.mark.anyio
async def test_get_all_with_mixed_case_search(repository, populated_db):
    """Test get_all with case-insensitive search"""
    # Arrange
    test_name = "UniqueSearchTerm"
    await repository.create(
        {
            "name": test_name.upper(),
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        }
    )

    filters = BaseFilterParams(search=test_name.lower())

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 1
    assert results[0].name == test_name.upper()


@pytest.mark.anyio
async def test_get_all_with_id_in_filter(repository, populated_db):
    """Test get_all with id__in filter"""
    # Arrange
    org_1_items = [item for item in populated_db]
    selected_ids = [str(item.id) for item in org_1_items[:2]]  # Take first two items

    filters = BaseFilterParams(id__in=selected_ids)

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == len(selected_ids)
    result_ids = [str(result.id) for result in results]
    assert all(id in selected_ids for id in result_ids)
