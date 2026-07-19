import pytest

from app.domains.users.factory import UserFactory
from app.domains.users.filters import UserFilter
from app.domains.users.repository import UserRepository
from app.domains.users.schemas import RoleEnum


async def create_test_users(db_session):
    """Create a set of users with distinct email/role/clerk_id for filter tests."""
    user_1 = await UserFactory.create_async(session=db_session, role=RoleEnum.ADMIN)
    user_2 = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    user_3 = await UserFactory.create_async(session=db_session, role=RoleEnum.STANDARD)
    return [user_1, user_2, user_3]


@pytest.mark.anyio
async def test_get_all_filters_by_email(db_session):
    # Arrange
    users = await create_test_users(db_session)
    repository = UserRepository(db_session)
    filters = UserFilter(email=users[0].email)

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 1
    assert results[0].id == users[0].id


@pytest.mark.anyio
async def test_get_all_filters_by_role(db_session):
    # Arrange
    users = await create_test_users(db_session)
    repository = UserRepository(db_session)
    filters = UserFilter(role=RoleEnum.ADMIN)

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 1
    assert results[0].id == users[0].id
    assert all(result.role == RoleEnum.ADMIN for result in results)


@pytest.mark.anyio
async def test_get_all_filters_by_clerk_id(db_session):
    # Arrange
    users = await create_test_users(db_session)
    repository = UserRepository(db_session)
    filters = UserFilter(clerk_id=users[1].clerk_id)

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 1
    assert results[0].id == users[1].id


@pytest.mark.anyio
async def test_get_all_filters_no_match(db_session):
    # Arrange
    await create_test_users(db_session)
    repository = UserRepository(db_session)
    filters = UserFilter(email="nonexistent@example.com")

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 0


@pytest.mark.anyio
async def test_get_all_filters_combined_with_id_in(db_session):
    # Arrange
    users = await create_test_users(db_session)
    repository = UserRepository(db_session)
    selected_ids = [str(users[1].id), str(users[2].id)]
    filters = UserFilter(id__in=selected_ids, role=RoleEnum.STANDARD)

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    result_ids = {str(result.id) for result in results}
    assert result_ids == set(selected_ids)
    assert all(result.role == RoleEnum.STANDARD for result in results)


@pytest.mark.anyio
async def test_get_all_filters_combined_id_in_excludes_non_matching_role(db_session):
    # Arrange
    users = await create_test_users(db_session)
    repository = UserRepository(db_session)
    # user_1 is admin, but we filter id__in to include it while also filtering role=standard
    selected_ids = [str(users[0].id), str(users[1].id)]
    filters = UserFilter(id__in=selected_ids, role=RoleEnum.STANDARD)

    # Act
    results = await repository.get_all(filters=filters)

    # Assert
    assert len(results) == 1
    assert results[0].id == users[1].id
