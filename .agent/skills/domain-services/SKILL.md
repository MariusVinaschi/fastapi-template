---
name: domain-services
description: Use when creating or modifying business logic and permission enforcement under app/domains/**/service.py. Do not use for repository query scoping, ORM definitions, API routes, or worker orchestration.
---

# Domain services

Services contain framework-agnostic business logic and permission enforcement. Follow `app/domains/users/service.py`, `app/domains/sessions/service.py`, and `app/domains/base/service.py`.

## Structure and reuse

- Compose only needed generic `*ServiceMixin[Model, Repository]` types and set `repository_class` plus `not_found_exception`:
  ```python
  class UserService(
      ListServiceMixin[User, UserRepository],
      UpdateServiceMixin[User, UserRepository],
      CreateServiceMixin[User, UserRepository],
      DeleteServiceMixin[User, UserRepository],
  ):
      repository_class = UserRepository
      not_found_exception = UserNotFoundException
  ```
- Prefer base CRUD/Bulk methods (`get_by_id`, `get_paginated`, `create`, `update`, `delete`, `bulk_*`) before creating a custom method.

## Deny-by-default permissions

- For a simple permission set, extend the whitelist:
  ```python
  _default_allowed_user_actions = frozenset({"read", "list", "create"})
  ```
- For role or ownership logic, override the appropriate hook. System operations return early; user-context paths assert a context and every forbidden action raises `PermissionDenied`:
  ```python
  def _check_general_permissions(self, action: str) -> bool:
      if self._is_system_operation():
          return True
      assert self.authorization_context is not None
      if self.authorization_context.user_role == RoleEnum.ADMIN:
          return True
      if action in ("read", "update"):
          return True
      raise PermissionDenied("Action not allowed")
  ```
  Use the same shape in `_check_instance_permissions(action, instance)` for row ownership.

Every public method first calls `_check_general_permissions(action)`. A row operation loads with `get_by_id` (which raises the configured not-found exception), then calls `_check_instance_permissions(action, instance)`. Custom reads follow the same ritual.

Inject `created_by` and `updated_by` through `_prepare_*_data`, never models or routes. Raise domain exceptions, never `HTTPException`. For another domain, use its service on the same session/context—never its repository.
