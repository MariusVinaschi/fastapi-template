---
name: domain-repositories
description: Use when creating or modifying domain data-access code under app/domains/**/repository.py, including custom queries and filter application. Do not use for service permission logic, ORM model definitions, or API routes.
---

# Domain repositories

Repositories provide framework-agnostic data access. Follow `app/domains/users/repository.py` and the granular mixins in `app/domains/base/repository.py`.

## Structure

- Compose only needed `*RepositoryMixin`s (`ReadRepositoryMixin`, `ListRepositoryMixin`, `Create`/`Update`/`Delete`/`Bulk*`).
- Use an `(session, authorization_context=None)` initializer that hard-wires the model and scope strategy:
  ```python
  class UserRepository(CreateRepositoryMixin, UpdateRepositoryMixin,
                       DeleteRepositoryMixin, ReadRepositoryMixin, ListRepositoryMixin):
      def __init__(self, session, authorization_context=None):
          super().__init__(session, UserScopeStrategy(), User, authorization_context)
  ```

## Data security and filters

- Every custom read applies `self._apply_user_scope(query)` before execution, even
  when a user-context caller always passes their own id -- it's free defense in
  depth against a future caller that doesn't (see `APIKeyRepository.get_by_user_id`).
  For literal `select(...)` calls, `just architecture-check` (rule
  `unscoped-repository-read`) checks that the call is present, never that the query
  is correctly scoped; correctness stays a review concern.
  ```python
  query = select(self.model).where(self.model.email == email)
  query = self._apply_user_scope(query)
  ```
- A finder may skip scoping only when it is genuinely system-only (keyed on
  something unknown until the row is found, e.g. `APIKeyRepository.get_by_api_key_hash`):
  call `self._require_system()` first -- the rule accepts it natively, no
  suppression needed. When neither scoping nor `_require_system()` fits, a named
  `# ast-grep-ignore: unscoped-repository-read` exemption with its reason on the
  line above is the escape hatch (see `base/repository.py`'s `_build_list_query`).
- An `_apply_filters` override calls the base method first, then handles domain fields under an `isinstance` guard:
  ```python
  def _apply_filters(self, query, filters):
      query = super()._apply_filters(query, filters)
      if not isinstance(filters, UserFilter):
          return query
      if filters.email is not None:
          query = query.where(self.model.email == filters.email)
      return query
  ```

Never commit: mutations only flush or refresh (`just architecture-check`, rule `no-commit-in-domain`). Do not import another domain's model or repository; cross-domain behavior belongs in services. `just architecture-check` also decides the cross-domain import rule, so write it correctly rather than auditing it.
