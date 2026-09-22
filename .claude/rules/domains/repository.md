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

For literal `select(...)` calls, `just architecture-check` (rule
`unscoped-repository-read`) checks that this ritual is *present* — never that a
query is *correctly* scoped. Passing it is not evidence of correctness; scoping logic
is still a review concern.

- **Every custom read must call `self._apply_user_scope(query)`** before executing:
  ```python
  query = select(self.model).where(self.model.email == email)
  query = self._apply_user_scope(query)
  ```
- A finder may intentionally skip scoping only for a genuinely system-only lookup
  (e.g. `APIKeyRepository.get_by_api_key_hash`, keyed on a hash unknown until the
  row is found). Call `self._require_system()` first — the rule accepts it natively,
  no suppression comment needed. A finder a user-context caller can legitimately
  reach must still be scoped, even redundantly, as defense in depth (see
  `APIKeyRepository.get_by_user_id`).
- The rule's own unscoped builders (`base/repository.py`'s `_build_list_query` /
  `_build_single_query`, whose callers apply the scope) are the pattern for a named,
  reasoned `# ast-grep-ignore: unscoped-repository-read` exemption when neither
  scoping nor `_require_system()` fits.

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
  transaction. Machine-checked (rule `no-commit-in-domain`).
- Stay in-domain: don't import another domain's models or repository (see `overview.md`).
