---
paths:
  - "app/domains/**/service.py"
---

# Service rules

Business logic + permission enforcement. Framework-agnostic. Reference:
`app/domains/users/service.py`, `app/domains/sessions/service.py`.

## Structure

- Compose the granular `*ServiceMixin[Model, Repository]` mixins you actually use
  (`ListServiceMixin`, `CreateServiceMixin`, …) from `app/domains/base/service.py`.
- Set the two class attributes: `repository_class = <Repository>` and
  `not_found_exception = <DomainNotFoundException>`.

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

## Reuse before writing

Prefer the base CRUD/Bulk methods (`get_by_id`, `get_paginated`, `create`, `update`,
`delete`, `bulk_*`). Write a custom method only when the behavior isn't covered.

## Permissions (deny-by-default)

- Simple whitelist — extend the frozenset, don't override a method:
  ```python
  _default_allowed_user_actions = frozenset({"read", "list", "create"})
  ```
- Role/ownership logic — override the hooks and follow the ritual:
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
  `_check_instance_permissions(action, instance)` follows the same shape for row-level
  ownership checks.
- Any user action that isn't whitelisted MUST raise `PermissionDenied`.

## Method contract

Every public method:
1. calls `self._check_general_permissions(<action>)` first;
2. for row operations, loads via `get_by_id` (raises `not_found_exception`), then calls
   `self._check_instance_permissions(<action>, instance)`.

Custom reads follow the same ritual — see `get_by_email` / `authenticate`.

## Also

- Audit fields (`created_by` / `updated_by`) are injected here via `_prepare_*_data`,
  never in models or routes.
- Raise **domain exceptions**, never `HTTPException`.
- Cross-domain work goes through the other domain's service, never its repository
  (see `overview.md`).
