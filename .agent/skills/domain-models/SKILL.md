---
name: domain-models
description: Use when creating or modifying Python SQLAlchemy ORM models under app/domains/**/models.py. Do not use for schemas, repositories, services, or unrelated Python files.
---

# Domain ORM models

Keep models framework-agnostic SQLAlchemy ORM only. Follow `app/domains/users/models.py` and the mixins in `app/domains/base/models.py`.

## Composition

- Inherit `Base` first, then compose mixins:
  ```python
  class User(Base, UUIDMixin, TimestampMixin, CreatedByMixin):
      __tablename__ = "users"
  ```
- `UUIDMixin` supplies the UUID primary key; `TimestampMixin` supplies timezone-aware `created_at` and `updated_at`.
- Use `CreatedByMixin` for user-editable entities only. Omit it for system-managed entities such as `APIKey` and `RefreshSession`.

## Conventions

- Use explicit plural snake_case `__tablename__` values.
- Never hand-name constraints: shared `MetaData` naming derives them.
- Model an enum with SQLAlchemy `Enum(..., name=..., create_constraint=True, validate_strings=True)` and a module-level `Literal` type alias.
- Put `back_populates` on both sides of a relationship. Owned children use `cascade="all, delete-orphan"`; one-to-one relationships use `uselist=False`.
- Avoid circular imports with `TYPE_CHECKING` and string relationships such as `relationship("User")`.
- Persist secrets only as hashes (`password_hash`, `key_hash`, `token_hash`), never raw values.
