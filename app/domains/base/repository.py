"""
Base repository - Framework agnostic data access layer.
Contains all the generic CRUD operations for domain entities.
"""

from collections.abc import Sequence
from typing import Generic, Optional, Tuple, Type, TypeVar

from sqlalchemy import Select, delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.authorization import (
    AuthorizationContext,
    AuthorizationScopeStrategy,
)
from app.domains.base.filters import BaseFilterParams
from app.domains.base.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common functionality for all entities"""

    def __init__(
        self,
        session: AsyncSession,
        scope_strategy: AuthorizationScopeStrategy,
        model: Type[ModelType],
        authorization_context: AuthorizationContext | None = None,
    ):
        self.session = session
        self.scope_strategy = scope_strategy
        self.model = model
        self.authorization_context = authorization_context

    async def _commit(self):
        """
        Commit the current transaction and handle exceptions.
        """
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e
        except Exception as e:
            await self.session.rollback()
            raise e

    def _apply_user_scope(self, query: Select) -> Select:
        """Apply user scope using the repository's authorization context"""
        if self.authorization_context is None:
            return query

        return self.scope_strategy.apply_scope(query, self.authorization_context)

    def _is_system_operation(self) -> bool:
        """Check if this is a system operation (no authorization context)"""
        return self.authorization_context is None


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

    async def get_paginated(self, filters: BaseFilterParams) -> Tuple[int, Sequence[ModelType]]:
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

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get entity by ID with optional authorization"""
        query = self._build_single_query().where(self.model.id == id)
        query = self._apply_user_scope(query)
        result = await self.session.scalars(query)
        return result.one_or_none()


class CreateRepositoryMixin(BaseRepository):
    """Mixin for create operations"""

    async def create(self, data: dict) -> ModelType:
        """
        Create a new instance in the database.
        """
        instance = self.model(**data)
        self.session.add(instance)
        await self._commit()
        await self.session.refresh(instance)
        return instance


class UpdateRepositoryMixin(BaseRepository):
    """Mixin for update operations"""

    async def update(self, instance: ModelType, data: dict) -> ModelType:
        """
        Update an existing instance in the database.
        """
        for key, value in data.items():
            setattr(instance, key, value)

        self.session.add(instance)
        await self._commit()
        await self.session.refresh(instance)
        return instance


class DeleteRepositoryMixin(BaseRepository):
    """Mixin for delete operations"""

    async def delete(self, instance: ModelType):
        await self.session.delete(instance)
        await self._commit()
        return True


class BulkUpdateRepositoryMixin(BaseRepository):
    """Mixin for bulk update operations"""

    async def bulk_update(self, instances: list[ModelType], data: dict) -> list[ModelType]:
        """
        Update multiple instances in the database with the same data.

        Args:
            instances: List of model instances to update
            data: Dictionary containing updates to apply to all instances

        Returns:
            list[ModelType]: List of updated model instances
        """
        if not instances:
            return []

        # Update attributes for each instance
        for instance in instances:
            for key, value in data.items():
                setattr(instance, key, value)
            self.session.add(instance)

        # Commit all changes in one transaction
        await self._commit()

        # Refresh all instances to get updated values
        for instance in instances:
            await self.session.refresh(instance)

        return instances


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
        await self._commit()
        return instances


class BulkDeleteRepositoryMixin(BaseRepository):
    """Mixin for bulk delete operations"""

    async def bulk_delete(self, ids: list[str]) -> int:
        """
        Delete multiple instances from the database by their IDs.

        Args:
            ids: List of entity IDs to delete

        Returns:
            int: Number of deleted records

        Example:
            deleted_count = await repository.bulk_delete(["id1", "id2", "id3"])
        """
        if not ids:
            return 0

        stmt = delete(self.model).where(self.model.id.in_(ids)).execution_options(synchronize_session=False)

        # Execute deletion
        result = await self.session.execute(stmt)
        await self._commit()

        # Return number of deleted records
        return getattr(result, "rowcount", 0) or 0
