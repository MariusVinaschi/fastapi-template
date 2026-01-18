from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.authorization import AuthorizationContext, AuthorizationScopeStrategy
from app.domains.base.repository import (
    BulkCreateRepositoryMixin,
    BulkDeleteRepositoryMixin,
    BulkUpdateRepositoryMixin,
    CreateRepositoryMixin,
    DeleteRepositoryMixin,
    ListRepositoryMixin,
    ReadRepositoryMixin,
    UpdateRepositoryMixin,
)
from app.domains.base.service import (
    BulkCreateServiceMixin,
    BulkDeleteServiceMixin,
    BulkUpdateServiceMixin,
    CreateServiceMixin,
    DeleteServiceMixin,
    ListServiceMixin,
    UpdateServiceMixin,
)
from tests.core.models import TestModel, TestUser

# Test UUID constants for consistent ID usage across tests
USER_1_ID = uuid4()
USER_2_ID = uuid4()


class CreateModelSchema(BaseModel):
    """Schema for creating test entities"""

    name: str


class UpdateModelSchema(BaseModel):
    """Schema for updating test entities with optional fields"""

    name: str | None = None


class FakeAuthorizationContext(AuthorizationContext):
    def __init__(
        self,
        user_id: UUID,
        email: str = "test@example.com",
        role: str = "user",
    ):
        self._user_id = user_id
        self._user_email = email
        self._user_role = role

    @property
    def user_id(self) -> str:
        return str(self._user_id)

    @property
    def user_email(self) -> str:
        return self._user_email

    @property
    def user_role(self) -> str:
        return self._user_role


class TestScopeStrategy(AuthorizationScopeStrategy):
    def __init__(self, model):
        super().__init__(model)

    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        return query


class TestRepository(
    CreateRepositoryMixin,
    UpdateRepositoryMixin,
    DeleteRepositoryMixin,
    BulkCreateRepositoryMixin,
    BulkUpdateRepositoryMixin,
    BulkDeleteRepositoryMixin,
    ReadRepositoryMixin,
    ListRepositoryMixin,
):
    """Test repository with basic search functionality"""

    def _apply_search(self, query: Select, search: str) -> Select:
        return query.where(self.model.name.ilike(f"%{search}%"))


class TestService(
    CreateServiceMixin[TestModel, TestRepository],
    UpdateServiceMixin[TestModel, TestRepository],
    DeleteServiceMixin[TestModel, TestRepository],
    ListServiceMixin[TestModel, TestRepository],
    BulkCreateServiceMixin[TestModel, TestRepository],
    BulkUpdateServiceMixin[TestModel, TestRepository],
    BulkDeleteServiceMixin[TestModel, TestRepository],
): ...  # noqa


@pytest.fixture
def test_model():
    """Provides the test model class"""
    return TestModel


@pytest.fixture
def scope_strategy(test_model):
    """Creates a scope strategy instance for the test model"""
    return TestScopeStrategy(test_model)


@pytest.fixture
async def repository(db_session, scope_strategy, test_model):
    """
    Creates a test repository instance with database session and scope strategy.
    Used for direct repository testing.
    """
    return TestRepository(
        session=db_session, scope_strategy=scope_strategy, model=test_model
    )


@pytest.fixture
def service_factory(db_session, scope_strategy, test_model):
    """
    Creates a factory that builds services with an authorization context.
    Uses a repository class factory to inject scope strategy and model.
    """

    def create_repository_class():
        class ConfiguredTestRepository(TestRepository):
            def __init__(self, session: AsyncSession, authorization_context=None):
                super().__init__(
                    session=session,
                    scope_strategy=scope_strategy,
                    model=test_model,
                    authorization_context=authorization_context,
                )

        return ConfiguredTestRepository

    def create_service(authorization_context=None):
        return TestService(
            session=db_session,
            repository_class=create_repository_class(),
            authorization_context=authorization_context,
        )

    return create_service


@pytest.fixture
async def user_1(db_session):
    """Creates and persists the first regular user"""
    user = TestUser(
        id=USER_1_ID,
        email="user1@test.com",
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_2(db_session):
    """Creates and persists the second regular user"""
    user = TestUser(
        id=USER_2_ID,
        email="user2@test.com",
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_context_user_1():
    """Creates an authorization context for user 1"""
    return FakeAuthorizationContext(
        user_id=USER_1_ID, email="user1@test.com", role="admin"
    )


@pytest.fixture
def auth_context_user_2():
    """Creates an authorization context for user 2"""
    return FakeAuthorizationContext(
        user_id=USER_2_ID, email="user2@test.com", role="user"
    )


@pytest.fixture
async def sample_data():
    """Provides simplified test data without organization dependencies"""
    return [
        {
            "name": "Test 1",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
        {
            "name": "Test 2",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
        {
            "name": "Test 3",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
        {
            "name": "Test 4",
            "created_by": "user1@test.com",
            "updated_by": "user1@test.com",
        },
    ]


@pytest.fixture
async def populated_db(repository, sample_data):
    """Populates the database with test data"""
    instances = await repository.bulk_create(sample_data)
    return instances
