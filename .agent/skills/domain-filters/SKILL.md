---
name: domain-filters
description: Use when creating or modifying framework-agnostic Pydantic filter parameters under app/domains/**/filters.py. Do not use for repository query code, response schemas, or API query dependencies.
---

# Domain filters

Filters are framework-agnostic Pydantic filter parameters. Follow `app/domains/users/filters.py` and `app/domains/base/filters.py`.

- Subclass `BaseFilterParams`, which already provides `limit`, `offset`, `search`, `order_by`, `id__in`, and `extra="forbid"`; never redefine those fields:
  ```python
  class UserFilter(BaseFilterParams):
      email: EmailStr | None = None
      role: RoleEnum | None = None
  ```
- Add domain fields as optional values with `None` defaults, using constrained types such as `EmailStr` and `StrEnum`.
- Name list-membership fields `<field>__in`.
- Repositories consume domain fields in `_apply_filters` with an `isinstance` guard; use the `domain-repositories` skill when changing that implementation.
- Omit `filters.py` entirely if the domain adds nothing beyond the base filter, as in `sessions/`.
