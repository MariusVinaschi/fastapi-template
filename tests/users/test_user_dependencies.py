import pytest
from pytest_mock import MockerFixture

from app.core.authorization import AuthorizationContext
from app.user.dependencies import get_auth_context, get_manager_auth_context
from app.user.factory import UserFactory
from app.user.models import UserAuthorizationAdapter


@pytest.mark.asyncio
async def test_get_auth_context_standard_user(mocker: MockerFixture, db_session):
    # Arrange
    user = await UserFactory.create_async(session=db_session, role="standard")
    mocker.patch(
        "app.security.auth.get_current_user",
        return_value=user,
    )

    # Act
    result = get_auth_context(user)

    # Assert
    assert isinstance(result, AuthorizationContext)
    assert isinstance(result, UserAuthorizationAdapter)
    assert result.user_id == str(user.id)
    assert result.user_email == user.email
    assert result.user_role == user.role


@pytest.mark.asyncio
async def test_get_manager_auth_context(mocker: MockerFixture, db_session):
    # Arrange
    manager_user = await UserFactory.create_async(session=db_session, role="manager")
    mocker.patch(
        "app.security.auth.get_current_manager_user",
        return_value=manager_user,
    )

    # Act
    result = get_manager_auth_context(manager_user)

    # Assert
    assert isinstance(result, AuthorizationContext)
    assert isinstance(result, UserAuthorizationAdapter)
    assert result.user_id == str(manager_user.id)
    assert result.user_email == manager_user.email
    assert result.user_role == manager_user.role


@pytest.mark.asyncio
async def test_get_auth_context_adapter_properties(db_session):
    # Arrange
    user = await UserFactory.create_async(
        session=db_session, email="test@example.com", role="standard"
    )

    # Act
    adapter = UserAuthorizationAdapter(user)

    # Assert
    assert adapter.user_id == str(user.id)
    assert adapter.user_email == "test@example.com"
    assert adapter.user_role == "standard"
