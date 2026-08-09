---
paths:
  - "app/domains/**/filters.py"
---

# Filter rules

Framework-agnostic Pydantic filter params. Reference: `app/domains/users/filters.py`,
base in `app/domains/base/filters.py`.

## Rules

- Subclass `BaseFilterParams` (which provides `limit`, `offset`, `search`, `order_by`,
  `id__in` and `extra="forbid"` — never redefine these):
  ```python
  class UserFilter(BaseFilterParams):
      email: EmailStr | None = None
      role: RoleEnum | None = None
  ```
- Add domain fields as `Optional` with `None` defaults; reuse constrained types
  (`EmailStr`, `StrEnum`).
- Use the `<field>__in` naming convention for list-membership filters.
- The repository consumes these in `_apply_filters` under an `isinstance` guard
  (see `repository.md`).
- Omit `filters.py` entirely when a domain adds no filters beyond the base (like
  `sessions/`).
