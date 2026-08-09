---
paths:
  - "app/domains/**/models.py"
---

# Model rules

Framework-agnostic SQLAlchemy ORM only. Reference: `app/domains/users/models.py`, base
mixins in `app/domains/base/models.py`.

## Composition

- Inherit `Base` first, then compose mixins:
  ```python
  class User(Base, UUIDMixin, TimestampMixin, CreatedByMixin):
      __tablename__ = "users"
  ```
- `UUIDMixin` → UUID PK. `TimestampMixin` → tz-aware `created_at` / `updated_at`.
- `CreatedByMixin` (audit-author `created_by` / `updated_by`) only on **user-editable**
  entities. Omit it for system-managed ones (`APIKey`, `RefreshSession`).

## Conventions

- Explicit plural snake_case `__tablename__`.
- Never hand-name constraints — the shared `MetaData` naming convention derives them.
- Enums: SQLAlchemy `Enum(..., name=..., create_constraint=True, validate_strings=True)`
  backed by a module-level `Literal` type alias (Python-level `Literal`, DB-level `Enum`).
- Relationships use `back_populates` on both sides; owned children
  `cascade="all, delete-orphan"`; one-to-one `uselist=False`.
- Avoid circular imports with `TYPE_CHECKING` + a string relationship
  (`relationship("User")`).
- Store secrets **hashed** (`password_hash`, `key_hash`, `token_hash`) — never raw.
