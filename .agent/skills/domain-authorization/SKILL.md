---
name: domain-authorization
description: Use when creating or modifying authorization scope strategies or identity context adapters under app/domains/**/authorization.py. Do not use for service-level permission checks, repository query implementations, or API authentication dependencies.
---

# Domain authorization

This module defines framework-agnostic query scoping and, only for identity sources, the model adapter to `AuthorizationContext`. Follow `app/domains/users/authorization.py` and `app/domains/base/authorization.py`.

## Scope strategy

- Each entity has one `AuthorizationScopeStrategy`; its no-argument initializer passes the model to the base class:
  ```python
  class APIKeyScopeStrategy(AuthorizationScopeStrategy):
      def __init__(self):
          super().__init__(APIKey)

      def apply_scope(self, query, context):
          return query.where(self.model.user_id == context.user_id)
  ```
- `apply_scope` always receives a non-None context: the repository handles the system case. Decide how to scope, not whether to scope.
- Global entities return the original query; owner-scoped entities filter their owner FK against `context.user_id`. The repository wires the strategy in its initializer.

## Identity adapters

Only an entity that authenticates a request needs an `AuthorizationContext` adapter exposing `user_id`, `user_email`, and `user_role`:

```python
class UserAuthorizationAdapter(AuthorizationContext):
    def __init__(self, user: User):
        self._user = user

    @property
    def user_id(self) -> str:
        return str(self._user.id)
```

Non-identity entities such as API keys and sessions require a scope strategy but no adapter.
