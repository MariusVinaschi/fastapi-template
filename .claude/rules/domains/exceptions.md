---
paths:
  - "app/domains/**/exceptions.py"
---

# Exception rules

Framework-agnostic domain exceptions — the domain layer's only outward contract.
Reference: `app/domains/users/exceptions.py`, base in `app/domains/base/exceptions.py`.

## Rules

- **Not-found** classes must extend `EntityNotFoundException` — `BaseService.not_found_exception`
  is typed `type[EntityNotFoundException]`, so anything else won't fit:
  ```python
  class UserNotFoundException(EntityNotFoundException):
      def __init__(self, message: str = "User not found") -> None:
          super().__init__(message)
  ```
- Other domain errors extend `DomainException` directly (e.g. `InvalidCredentialsError`).
- One class per failure mode, each overriding `__init__` with a domain-specific default
  message.
- You may note the intended HTTP mapping in the docstring (e.g. "Mapped to HTTP 401 by the
  delivery layer"), but the mapping itself lives in `app/api/`, never here.
- Never import from `app/api/` or raise `HTTPException`.
