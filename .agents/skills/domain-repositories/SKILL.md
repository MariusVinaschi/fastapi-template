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

- Every custom read applies `self._apply_user_scope(query)` before execution:
  ```python
  query = select(self.model).where(self.model.email == email)
  query = self._apply_user_scope(query)
  ```
- A finder may skip scoping only for an authentication/system lookup (for example, `APIKeyRepository.get_by_api_key_hash`). Document why inline and ensure its service performs the permission check.
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

Never commit: mutations only flush or refresh. Do not import another domain's model or repository; cross-domain behavior belongs in services.
