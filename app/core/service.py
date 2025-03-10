from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import AuthorizationContext
from app.core.exceptions import EntityNotFoundException
from app.core.filters import BaseFilterParams
from app.core.repository import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
BulkUpdateSchemaType = TypeVar("BulkUpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, RepositoryType]):
    def __init__(
        self,
        session: AsyncSession,
        repository_class: Type[RepositoryType],
        not_found_exception: Type[EntityNotFoundException] = EntityNotFoundException,
    ):
        self.session = session
        self.repository = repository_class(session)
        self.not_found_exception = not_found_exception

    def _check_general_permissions(
        self,
        action: str,
        authorization_context: AuthorizationContext,
    ) -> bool:
        return True

    def _check_instance_permissions(
        self,
        action: str,
        authorization_context: AuthorizationContext,
        instance: ModelType,
    ) -> bool:
        return True

    async def get_by_id(
        self, id: UUID, authorization_context: AuthorizationContext
    ) -> Optional[ModelType]:
        """Get entity by ID with access control"""
        self._check_general_permissions("read", authorization_context)

        instance = await self.repository.get_by_id(
            id=id, authorization_context=authorization_context
        )
        if not instance:
            raise self.not_found_exception(f"Entity with id {id} not found")

        self._check_instance_permissions("read", authorization_context, instance)

        return instance


class ListServiceMixin(BaseService[ModelType, RepositoryType]):
    async def get_paginated(
        self, authorization_context: AuthorizationContext, filters: BaseFilterParams
    ) -> dict:
        """Get paginated entities with access control"""
        self._check_general_permissions("list", authorization_context)
        total_count, items = await self.repository.get_paginated(
            authorization_context=authorization_context, filters=filters
        )
        return {"count": total_count, "data": items}


class CreateServiceMixin(BaseService[ModelType, RepositoryType]):
    def _prepare_create_data(
        self, data: CreateSchemaType, authorization_context: AuthorizationContext
    ) -> dict:
        """Prepare data for creation - override in subclass if needed"""
        return {
            **data.model_dump(),
            "created_by": authorization_context.user_email,
            "updated_by": authorization_context.user_email,
        }

    async def _validate_create(
        self, data: dict, authorization_context: AuthorizationContext
    ) -> None:
        """Validate creation - override in subclass if needed"""
        return True

    async def create(
        self, data: CreateSchemaType, authorization_context: AuthorizationContext
    ) -> ModelType:
        """Create new entity"""
        self._check_general_permissions("create", authorization_context)

        # Prepare data - override in subclass if needed
        create_data = self._prepare_create_data(data, authorization_context)

        # Validate creation - override in subclass if needed
        await self._validate_create(create_data, authorization_context)

        return await self.repository.create(create_data)


class UpdateServiceMixin(BaseService[ModelType, RepositoryType]):
    def _prepare_update_data(
        self, data: UpdateSchemaType, authorization_context: AuthorizationContext
    ) -> dict:
        """Prepare data for update - override in subclass if needed"""
        return {
            **data.model_dump(exclude_unset=True),
            "updated_by": authorization_context.user_email,
        }

    async def _validate_update(
        self,
        instance: ModelType,
        data: dict,
        authorization_context: AuthorizationContext,
    ) -> None:
        """Validate update - override in subclass if needed"""
        return True

    async def update(
        self,
        id: UUID,
        data: UpdateSchemaType,
        authorization_context: AuthorizationContext,
    ) -> Optional[ModelType]:
        """Update existing entity"""
        self._check_general_permissions("update", authorization_context)

        # Get existing instance
        instance = await self.get_by_id(id, authorization_context)

        self._check_instance_permissions("update", authorization_context, instance)

        # Prepare update data - override in subclass if needed
        update_data = self._prepare_update_data(data, authorization_context)

        # Validate update - override in subclass if needed
        await self._validate_update(instance, update_data, authorization_context)

        return await self.repository.update(instance, update_data)


class DeleteServiceMixin(BaseService[ModelType, RepositoryType]):
    async def delete(
        self, id: UUID, authorization_context: AuthorizationContext
    ) -> bool:
        """Delete entity"""
        self._check_general_permissions("delete", authorization_context)

        instance = await self.get_by_id(id, authorization_context)

        self._check_instance_permissions("delete", authorization_context, instance)

        return await self.repository.delete(instance)


class BulkUpdateServiceMixin(BaseService[ModelType, RepositoryType]):
    def _prepare_bulk_update_data(
        self, data: UpdateSchemaType, authorization_context: AuthorizationContext
    ) -> dict:
        """Prepare data for update - override in subclass if needed"""
        return {
            **data.model_dump(exclude_unset=True),
            "updated_by": authorization_context.user_email,
        }

    async def _validate_bulk_update(
        self,
        instances: list[ModelType],
        data: BulkUpdateSchemaType,
        authorization_context: AuthorizationContext,
    ) -> None:
        """
        Validate bulk update operation - override in subclass if needed.

        Args:
            instances: List of existing model instances
            data: Update data dictionary to apply to all instances
            authorization_context: AuthorizationContext performing the update

        Raises:
            ValidationError: If validation fails
        """
        for instance in instances:
            await self._validate_update(instance, data, authorization_context)

        return True

    async def bulk_update(
        self,
        ids: list[UUID],
        data: BulkUpdateSchemaType,
        authorization_context: AuthorizationContext,
        filter_class: Type[BaseFilterParams] = BaseFilterParams,
    ) -> list[ModelType]:
        """
        Update multiple entities with the same data in a single operation.

        Args:
            ids: List of entity IDs to update
            data: Update data to apply to all entities
            authorization_context: AuthorizationContext performing the update

        Returns:
            List of updated entities

        Raises:
            EntityNotFoundException: If any entity is not found
            ValidationError: If validation fails for any entity
        """
        self._check_general_permissions("bulk_update", authorization_context)

        # Fetch all instances in a single query
        filters = filter_class(id__in=[str(id) for id in ids], limit=100)
        instances = await self.repository.get_all(
            authorization_context=authorization_context,
            filters=filters,
        )

        # Verify all requested entities were found
        if len(instances) != len(ids):
            found_ids = {str(instance.id) for instance in instances}
            missing_ids = [str(id) for id in ids if str(id) not in found_ids]
            raise self.not_found_exception(
                f"Entities with ids {', '.join(missing_ids)} not found"
            )

        # Prepare update data once
        update_data = self._prepare_bulk_update_data(data, authorization_context)

        # Validate the bulk update operation
        await self._validate_bulk_update(instances, update_data, authorization_context)

        # Perform bulk update via repository
        updated_instances = await self.repository.bulk_update(
            instances=instances, data=update_data
        )

        return updated_instances


class BulkDeleteServiceMixin(BaseService[ModelType, RepositoryType]):
    async def _validate_bulk_delete(
        self, ids: list[UUID], authorization_context: AuthorizationContext
    ) -> None:
        """Validate bulk deletion - override in subclass if needed"""
        return True

    async def bulk_delete(
        self, ids: list[UUID], authorization_context: AuthorizationContext
    ) -> bool:
        """Bulk delete entities"""
        self._check_general_permissions("bulk_delete", authorization_context)

        # Validate deletion - override in subclass if needed
        await self._validate_bulk_delete(ids, authorization_context)

        return await self.repository.bulk_delete(ids)


class BulkCreateServiceMixin(BaseService[ModelType, RepositoryType]):
    def _prepare_bulk_create_data(
        self, data: CreateSchemaType, authorization_context: AuthorizationContext
    ) -> dict:
        """Prepare data for creation - override in subclass if needed"""
        return {
            **data.model_dump(),
            "created_by": authorization_context.user_email,
            "updated_by": authorization_context.user_email,
        }

    async def _validate_bulk_create(
        self, items: list[dict], authorization_context: AuthorizationContext
    ) -> None:
        """
        Validate multiple items at once.
        Override in subclass if needed.
        """
        for item in items:
            await self._validate_create(item, authorization_context)

    async def bulk_create(
        self, data: list[CreateSchemaType], authorization_context: AuthorizationContext
    ) -> list[ModelType]:
        """Create multiple entities"""
        self._check_general_permissions("bulk_create", authorization_context)

        # Prepare data - override in subclass if needed
        create_data = [
            self._prepare_bulk_create_data(item, authorization_context) for item in data
        ]

        # Validate creation - override in subclass if needed
        await self._validate_bulk_create(create_data, authorization_context)

        return await self.repository.bulk_create(create_data)
