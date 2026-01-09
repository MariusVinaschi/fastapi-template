"""
Base service - Framework agnostic business logic layer.
Contains all the generic CRUD operations and business rules.
"""
from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base.authorization import AuthorizationContext
from app.domains.base.exceptions import EntityNotFoundException
from app.domains.base.filters import BaseFilterParams
from app.domains.base.repository import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
BulkUpdateSchemaType = TypeVar("BulkUpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, RepositoryType]):
    """Base service with common functionality for all entities"""

    def __init__(
        self,
        session: AsyncSession,
        repository_class: Type[RepositoryType],
        authorization_context: AuthorizationContext | None = None,
        not_found_exception: Type[EntityNotFoundException] = EntityNotFoundException,
    ):
        self.session = session
        self.authorization_context = authorization_context
        self.repository = repository_class(session, authorization_context=authorization_context)
        self.not_found_exception = not_found_exception

    @classmethod
    def for_user(
        cls,
        session: AsyncSession,
        repository_class: Type[RepositoryType],
        authorization_context: AuthorizationContext,
        not_found_exception: Type[EntityNotFoundException] = EntityNotFoundException,
    ):
        """Factory method for user operations (with authorization)"""
        return cls(session, repository_class, authorization_context, not_found_exception)

    @classmethod
    def for_system(
        cls,
        session: AsyncSession,
        repository_class: Type[RepositoryType],
        not_found_exception: Type[EntityNotFoundException] = EntityNotFoundException,
    ):
        """Factory method for system operations (without authorization)"""
        return cls(session, repository_class, None, not_found_exception)

    def _is_system_operation(self) -> bool:
        """Check if this is a system operation (no authorization context)"""
        return self.authorization_context is None

    def _check_general_permissions(self, action: str) -> bool:
        """Check general permissions - override in subclass if needed"""
        return True

    def _check_instance_permissions(self, action: str, instance: ModelType) -> bool:
        """Check instance permissions - override in subclass if needed"""
        return True

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID with optional access control"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("read")

        instance = await self.repository.get_by_id(str(id))
        if not instance:
            raise self.not_found_exception(f"Entity with id {id} not found")

        # Check instance permissions only for user operations
        if not self._is_system_operation():
            self._check_instance_permissions("read", instance)

        return instance


class ListServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for list/pagination operations"""

    async def get_paginated(self, filters: BaseFilterParams) -> dict:
        """Get paginated entities with optional access control"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("list")

        total_count, items = await self.repository.get_paginated(filters)
        return {"count": total_count, "data": items}

    async def get_ids(self, filters: BaseFilterParams) -> list[UUID]:
        """Get IDs of entities with access control"""
        if not self._is_system_operation():
            self._check_general_permissions("list")
        return await self.repository.get_ids(filters=filters)

    async def get_all(self, filters: BaseFilterParams) -> list[ModelType]:
        """Get all entities with access control"""
        if not self._is_system_operation():
            self._check_general_permissions("list")
        return await self.repository.get_all(filters=filters)


class CreateServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for create operations"""

    def _prepare_create_data(self, data: CreateSchemaType) -> dict:
        """Prepare data for creation - override in subclass if needed"""
        result = data.model_dump()

        # Add created_by only for user operations
        if not self._is_system_operation():
            result["created_by"] = self.authorization_context.user_email
            result["updated_by"] = self.authorization_context.user_email
        else:
            result["created_by"] = "system"
            result["updated_by"] = "system"

        return result

    async def _validate_create(self, data: dict) -> None:
        """Validate creation - override in subclass if needed"""
        return True

    async def create(self, data: CreateSchemaType) -> ModelType:
        """Create new entity with optional authorization"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("create")

        # Prepare data - override in subclass if needed
        create_data = self._prepare_create_data(data)

        # Validate creation - override in subclass if needed
        await self._validate_create(create_data)

        return await self.repository.create(create_data)


class UpdateServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for update operations"""

    def _prepare_update_data(self, data: UpdateSchemaType) -> dict:
        """Prepare data for update - override in subclass if needed"""
        result = data.model_dump(exclude_unset=True)

        # Add updated_by only for user operations
        if not self._is_system_operation():
            result["updated_by"] = self.authorization_context.user_email
        else:
            result["updated_by"] = "system"

        return result

    async def _validate_update(self, instance: ModelType, data: dict) -> None:
        """Validate update - override in subclass if needed"""
        return True

    async def update(self, id: UUID, data: UpdateSchemaType) -> Optional[ModelType]:
        """Update existing entity with optional authorization"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("update")

        # Get existing instance
        instance = await self.get_by_id(id)

        # Check instance permissions only for user operations
        if not self._is_system_operation():
            self._check_instance_permissions("update", instance)

        # Prepare update data - override in subclass if needed
        update_data = self._prepare_update_data(data)

        # Validate update - override in subclass if needed
        await self._validate_update(instance, update_data)

        return await self.repository.update(instance, update_data)


class DeleteServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for delete operations"""

    async def delete(self, id: UUID) -> bool:
        """Delete entity with optional authorization"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("delete")

        instance = await self.get_by_id(id)

        # Check instance permissions only for user operations
        if not self._is_system_operation():
            self._check_instance_permissions("delete", instance)

        return await self.repository.delete(instance)


class BulkUpdateServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for bulk update operations"""

    def _prepare_bulk_update_data(self, data: UpdateSchemaType) -> dict:
        """Prepare data for update - override in subclass if needed"""
        result = data.model_dump(exclude_unset=True)

        # Add updated_by only for user operations
        if not self._is_system_operation():
            result["updated_by"] = self.authorization_context.user_email
        else:
            result["updated_by"] = "system"

        return result

    async def _validate_bulk_update(
        self, instances: list[ModelType], data: BulkUpdateSchemaType
    ) -> None:
        """
        Validate bulk update operation - override in subclass if needed.

        Args:
            instances: List of existing model instances
            data: Update data dictionary to apply to all instances

        Raises:
            ValidationError: If validation fails
        """
        for instance in instances:
            await self._validate_update(instance, data)

        return True

    async def bulk_update(
        self,
        ids: list[UUID],
        data: BulkUpdateSchemaType,
        filter_class: Type[BaseFilterParams] = BaseFilterParams,
    ) -> list[ModelType]:
        """
        Update multiple entities with the same data in a single operation.

        Args:
            ids: List of entity IDs to update
            data: Update data to apply to all entities

        Returns:
            List of updated entities

        Raises:
            EntityNotFoundException: If any entity is not found
            ValidationError: If validation fails for any entity
        """
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("bulk_update")

        # Fetch all instances in a single query
        filters = filter_class(id__in=[str(id) for id in ids], limit=100)
        instances = await self.repository.get_all(filters)

        # Verify all requested entities were found
        if len(instances) != len(ids):
            found_ids = {str(instance.id) for instance in instances}
            missing_ids = [str(id) for id in ids if str(id) not in found_ids]
            raise self.not_found_exception(f"Entities with ids {', '.join(missing_ids)} not found")

        # Prepare update data once
        update_data = self._prepare_bulk_update_data(data)

        # Validate the bulk update operation
        await self._validate_bulk_update(instances, update_data)

        # Perform bulk update via repository
        updated_instances = await self.repository.bulk_update(instances=instances, data=update_data)

        return updated_instances


class BulkDeleteServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for bulk delete operations"""

    async def _validate_bulk_delete(self, ids: list[UUID]) -> None:
        """Validate bulk deletion - override in subclass if needed"""
        return True

    async def bulk_delete(self, ids: list[UUID]) -> bool:
        """Bulk delete entities with optional authorization"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("bulk_delete")

        # Validate deletion - override in subclass if needed
        await self._validate_bulk_delete(ids)

        return await self.repository.bulk_delete(ids)


class BulkCreateServiceMixin(BaseService[ModelType, RepositoryType]):
    """Mixin for bulk create operations"""

    def _prepare_bulk_create_data(self, data: CreateSchemaType) -> dict:
        """Prepare data for creation - override in subclass if needed"""
        result = data.model_dump()

        # Add created_by only for user operations
        if not self._is_system_operation():
            result["created_by"] = self.authorization_context.user_email
            result["updated_by"] = self.authorization_context.user_email
        else:
            result["created_by"] = "system"
            result["updated_by"] = "system"

        return result

    async def _validate_bulk_create(self, items: list[dict]) -> None:
        """
        Validate multiple items at once.
        Override in subclass if needed.
        """
        for item in items:
            await self._validate_create(item)

    async def bulk_create(self, data: list[CreateSchemaType]) -> list[ModelType]:
        """Create multiple entities with optional authorization"""
        # Check permissions only for user operations
        if not self._is_system_operation():
            self._check_general_permissions("bulk_create")

        # Prepare data - override in subclass if needed
        create_data = [self._prepare_bulk_create_data(item) for item in data]

        # Validate creation - override in subclass if needed
        await self._validate_bulk_create(create_data)

        return await self.repository.bulk_create(create_data)

