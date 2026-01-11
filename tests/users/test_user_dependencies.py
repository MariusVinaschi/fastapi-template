import pytest
from pytest_mock import MockerFixture

from app.domains.base.authorization import AuthorizationContext
from app.api.dependencies import get_auth_context, get_admin_auth_context
from app.domains.users.factory import UserFactory
from app.domains.users.models import UserAuthorizationAdapter


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
async def test_get_admin_auth_context(mocker: MockerFixture, db_session):
    # Arrange
    admin_user = await UserFactory.create_async(session=db_session, role="admin")
    mocker.patch(
        "app.security.auth.get_current_admin_user",
        return_value=admin_user,
    )

    # Act
    result = get_admin_auth_context(admin_user)

    # Assert
    assert isinstance(result, AuthorizationContext)
    assert isinstance(result, UserAuthorizationAdapter)
    assert result.user_id == str(admin_user.id)
    assert result.user_email == admin_user.email
    assert result.user_role == admin_user.role


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
