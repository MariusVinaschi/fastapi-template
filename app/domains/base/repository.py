"""
Base repository - Framework agnostic data access layer.
Contains all the generic CRUD operations for domain entities.
"""

from collections.abc import Sequence
from typing import Generic, Protocol, TypeVar, cast

from sqlalchemy import Select, delete, func, insert, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.authorization import (
    AuthorizationContext,
    AuthorizationScopeStrategy,
)
from app.domains.base.exceptions import SystemOperationRequired
from app.domains.base.filters import BaseFilterParams
from app.domains.base.models import Base

ModelType = TypeVar("ModelType", bound=Base)
RepositoryType = TypeVar("RepositoryType", bound="BaseRepository")


class RepositoryFactory(Protocol[RepositoryType]):
    """
    Protocol for repository classes that can be instantiated with only
    session and optional authorization_context (concrete repos inject
    scope_strategy and model in their own __init__).
    """

    def __call__(
        self,
        session: AsyncSession,
        *,
        authorization_context: AuthorizationContext | None = None,
    ) -> RepositoryType: ...


class SupportsId(Protocol):
    id: object


class BaseRepository(Generic[ModelType]):  # noqa: UP046 -- module-level `ModelType`/`RepositoryType` TypeVars are
    # shared with `RepositoryFactory` above and every `*Mixin(BaseRepository)` subclass below; switching this one
    # class to PEP 695 `class Foo[T]` scoping would desync it from those, requiring a wider generics refactor.
    """Base repository with common functionality for all entities"""

    def __init__(
        self,
        session: AsyncSession,
        scope_strategy: AuthorizationScopeStrategy,
        model: type[ModelType],
        authorization_context: AuthorizationContext | None = None,
    ):
        self.session = session
        self.scope_strategy = scope_strategy
        self.model = model
        self.authorization_context = authorization_context

    def _apply_user_scope(self, query: Select) -> Select:
        """Apply user scope using the repository's authorization context"""
        if self.authorization_context is None:
            return query

        return self.scope_strategy.apply_scope(query, self.authorization_context)

    def _is_system_operation(self) -> bool:
        """Check if this is a system operation (no authorization context)"""
        return self.authorization_context is None

    def _require_system(self) -> None:
        """Raise SystemOperationRequired if called with a user authorization context."""
        if not self._is_system_operation():
            raise SystemOperationRequired("This repository method requires system context (no authorization_context)")

    async def get_by_id(self, id: str) -> ModelType | None:
        raise NotImplementedError

    async def get_all(self, filters: BaseFilterParams) -> Sequence[ModelType]:
        raise NotImplementedError

    async def get_paginated(self, filters: BaseFilterParams) -> tuple[int, Sequence[ModelType]]:
        raise NotImplementedError

    async def get_ids(self, filters: BaseFilterParams) -> Sequence[str]:
        raise NotImplementedError

    async def create(self, data: dict) -> ModelType:
        raise NotImplementedError

    async def update(self, instance: ModelType, data: dict) -> ModelType:
        raise NotImplementedError

    async def delete(self, instance: ModelType) -> bool:
        raise NotImplementedError

    async def bulk_update(self, instances: Sequence[ModelType], data: dict) -> Sequence[ModelType]:
        raise NotImplementedError

    async def bulk_delete(self, ids: list[str]) -> int:
        raise NotImplementedError

    async def bulk_create(self, data: list[dict]) -> Sequence[ModelType]:
        raise NotImplementedError


class ListRepositoryMixin(BaseRepository):
    """Mixin for list/pagination operations"""

    def _build_list_query(self) -> Select:
        """
        Build query for fetching multiple entities.
        Override this method to add specific joins for list fetches.
        """
        return select(self.model)

    async def get_all(self, filters: BaseFilterParams) -> Sequence[ModelType]:
        """Get all entities with optional authorization"""
        query = self._build_list_query()
        query = self._apply_user_scope(query)

        if filters.search:
            query = self._apply_search(query, filters.search)

        query = self._apply_ordering(query, filters.order_by)

        query = self._apply_filters(query, filters)
        result = await self.session.scalars(query)
        return result.fetchall()

    async def get_paginated(self, filters: BaseFilterParams) -> tuple[int, Sequence[ModelType]]:
        """Get paginated entities with optional authorization"""
        query = self._build_list_query()
        query = self._apply_user_scope(query)

        if filters.search:
            query = self._apply_search(query, filters.search)

        query = self._apply_ordering(query, filters.order_by)

        query = self._apply_filters(query, filters)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self.session.scalar(count_query)

        # Get paginated data
        paginated_query = query.offset(filters.offset).limit(filters.limit)
        results = await self.session.scalars(paginated_query)

        return total_count or 0, results.fetchall()

    async def get_ids(
        self,
        filters: BaseFilterParams,
    ) -> Sequence[str]:
        """
        Get only the IDs of entities matching the filters.
        This is more efficient than get_all() when only IDs are needed.

        Args:
            filters: The filters to apply

        Returns:
            list[str]: List of entity IDs
        """
        query = select(self.model.id)
        query = self._apply_user_scope(query)

        if filters.search:
            query = self._apply_search(query, filters.search)

        query = self._apply_filters(query, filters)
        result = await self.session.scalars(query)
        return result.fetchall()

    def _apply_search(self, query: Select, search: str) -> Select:
        """
        Apply global search filter.
        Override this method to implement search logic.
        """
        return query

    def _apply_filters(self, query: Select, filters: BaseFilterParams) -> Select:
        """
        Apply specific filters.
        Override this method to implement specific filter logic.
        """
        if filters.id__in:
            query = query.where(self.model.id.in_(filters.id__in))

        return query

    def _apply_ordering(self, query: Select, order_by: str | None) -> Select:
        """
        Apply ordering to the query

        Args:
            query: SQL query to be ordered
            order_by: Field to order by (e.g. "name" or "-name" for descending)
                    None will return the original query

        Returns:
            Query with ordering applied
        """
        if not order_by:
            return query

        # Extract field and direction from order_by string
        direction = "desc" if order_by.startswith("-") else "asc"
        field = order_by[1:] if order_by.startswith("-") or order_by.startswith("+") else order_by

        # Verify that the field exists on the model
        if not hasattr(self.model, field):
            return query

        # Apply ordering
        column = getattr(self.model, field)
        return query.order_by(column.desc() if direction == "desc" else column.asc())


class ReadRepositoryMixin(BaseRepository):
    """Mixin for read operations"""

    def _build_single_query(self) -> Select:
        """
        Build query for fetching a single entity.
        Override this method to add specific joins for single entity fetches.
        """
        return select(self.model)

    async def get_by_id(self, id: str) -> ModelType | None:
        """Get entity by ID with optional authorization"""
        query = self._build_single_query().where(self.model.id == id)
        query = self._apply_user_scope(query)
        result = await self.session.scalars(query)
        return result.one_or_none()


class CreateRepositoryMixin(BaseRepository):
    """Mixin for create operations"""

    async def create(self, data: dict) -> ModelType:
        """Stage a new instance; transaction boundary owned by the caller (route/worker)."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance


class UpdateRepositoryMixin(BaseRepository):
    """Mixin for update operations"""

    async def update(self, instance: ModelType, data: dict) -> ModelType:
        """Apply attribute changes; transaction boundary owned by the caller."""
        for key, value in data.items():
            setattr(instance, key, value)

        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance


class DeleteRepositoryMixin(BaseRepository):
    """Mixin for delete operations"""

    async def delete(self, instance: ModelType):
        await self.session.delete(instance)
        await self.session.flush()
        return True


class BulkUpdateRepositoryMixin(BaseRepository):
    """Mixin for bulk update operations"""

    async def bulk_update(self, instances: Sequence[ModelType], data: dict) -> Sequence[ModelType]:
        """
        Update multiple instances in the database with the same data.

        Uses a single UPDATE ... RETURNING * statement: one round-trip to apply the
        update and fetch the new column values, instead of N refresh calls after an
        ORM dirty-tracking commit.

        Args:
            instances: Model instances to update (read-only view — used for ID extraction)
            data: Dictionary containing updates to apply to all instances

        Returns:
            The sequence of refreshed instances (caller-visible).
        """
        if not instances:
            return []

        ids = [cast(SupportsId, instance).id for instance in instances]
        stmt = (
            sa_update(self.model)
            .where(self.model.id.in_(ids))
            .values(**data)
            .returning(self.model)
            .execution_options(synchronize_session=False, populate_existing=True)
        )
        result = await self.session.execute(stmt)
        refreshed = result.scalars().all()

        return refreshed


class BulkCreateRepositoryMixin(BaseRepository):
    """Mixin for bulk create operations"""

    async def bulk_create(self, data: list[dict]) -> Sequence[ModelType]:
        """
        Create multiple instances in the database and return created objects.

        Args:
            data: List of dictionaries containing model attributes

        Returns:
            list[ModelType]: List of created model instances with their IDs
        """

        if not data:
            return []

        result = await self.session.execute(
            insert(self.model).returning(self.model).execution_options(synchronize_session=False),
            data,
        )

        instances = result.scalars().all()
        return instances


class BulkDeleteRepositoryMixin(BaseRepository):
    """Mixin for bulk delete operations"""

    async def bulk_delete(self, ids: list[str]) -> int:
        """
        Delete multiple instances from the database by their IDs.

        When an authorization context is present, the delete is restricted to the
        subset of IDs visible through the scope strategy — this prevents a user from
        deleting rows belonging to another user/tenant by supplying their IDs.

        Args:
            ids: List of entity IDs to delete

        Returns:
            int: Number of deleted records
        """
        if not ids:
            return 0

        if self.authorization_context is not None:
            scoped_ids = self._apply_user_scope(select(self.model.id).where(self.model.id.in_(ids)))
            stmt = (
                delete(self.model)
                .where(self.model.id.in_(scoped_ids.scalar_subquery()))
                .execution_options(synchronize_session=False)
            )
        else:
            stmt = delete(self.model).where(self.model.id.in_(ids)).execution_options(synchronize_session=False)

        result = await self.session.execute(stmt)

        return getattr(result, "rowcount", 0) or 0
