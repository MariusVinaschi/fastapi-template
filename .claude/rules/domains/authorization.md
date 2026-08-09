---
paths:
  - "app/domains/**/authorization.py"
---

# Authorization rules

Defines HOW queries are scoped per entity, and (for identity sources) how a model maps to
an `AuthorizationContext`. Framework-agnostic. Reference:
`app/domains/users/authorization.py`, base in `app/domains/base/authorization.py`.

## Scope strategy (one per entity)

- Subclass `AuthorizationScopeStrategy` with a no-arg `__init__` passing the model up:
  ```python
  class APIKeyScopeStrategy(AuthorizationScopeStrategy):
      def __init__(self):
          super().__init__(APIKey)

      def apply_scope(self, query, context):
          return query.where(self.model.user_id == context.user_id)
  ```
- `apply_scope` **always receives a non-None context** — the repository's
  `_apply_user_scope` already handled the None (system) case. Decide only HOW to scope,
  never whether to.
- Global-visibility entity: `return query` unchanged.
- Owner-scoped entity: `return query.where(self.model.<owner_fk> == context.user_id)`.
- The repository wires the strategy in its `__init__` (see `repository.md`).

## Context adapter (only for identity sources)

If the entity is an identity source (something a request authenticates as), add an
`AuthorizationContext` adapter here exposing `user_id`, `user_email`, `user_role`:

```python
class UserAuthorizationAdapter(AuthorizationContext):
    def __init__(self, user: User):
        self._user = user

    @property
    def user_id(self) -> str:
        return str(self._user.id)
    ...
```

Non-identity entities (API keys, sessions) need a scope strategy but **no** adapter.
