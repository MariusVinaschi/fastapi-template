---
paths:
  - "app/domains/**/repository.py"
---

# Repository rules

Data access. Framework-agnostic. Reference: `app/domains/users/repository.py`, base
mixins in `app/domains/base/repository.py`.

## Structure

- Compose the granular `*RepositoryMixin` you need (`ReadRepositoryMixin`,
  `ListRepositoryMixin`, `Create`/`Update`/`Delete`/`Bulk*`).
- Collapse `__init__` to `(session, authorization_context=None)` and hard-wire the scope
  strategy + model:

```python
class UserRepository(CreateRepositoryMixin, UpdateRepositoryMixin,
                     DeleteRepositoryMixin, ReadRepositoryMixin, ListRepositoryMixin):
    def __init__(self, session, authorization_context=None):
        super().__init__(session, UserScopeStrategy(), User, authorization_context)
```

## Scoping (data security)

- **Every custom read must call `self._apply_user_scope(query)`** before executing:
  ```python
  query = select(self.model).where(self.model.email == email)
  query = self._apply_user_scope(query)
  ```
- A finder may intentionally skip scoping only for auth/system lookups (e.g.
  `APIKeyRepository.get_by_api_key_hash`). When it does, the **service** must enforce the
  permission check, and you document the reason inline.

## Filters

Overriding `_apply_filters` must call `super()._apply_filters(query, filters)` first (keeps
`id__in`), then guard domain fields with an `isinstance` check:

```python
def _apply_filters(self, query, filters):
    query = super()._apply_filters(query, filters)
    if not isinstance(filters, UserFilter):
        return query
    if filters.email is not None:
        query = query.where(self.model.email == filters.email)
    return query
```

## Invariants

- **Never `commit()`** — mutations `flush()` / `refresh()` only; the caller owns the
  transaction.
- Stay in-domain: don't import another domain's models or repository (see `overview.md`).
