---
name: domain-exceptions
description: Use when creating or modifying framework-agnostic domain exceptions under app/domains/**/exceptions.py. Do not use for FastAPI exception handlers, HTTP mappings, or unrelated error handling.
---

# Domain exceptions

Domain exceptions are the domain layer's only outward contract. Follow `app/domains/users/exceptions.py` and `app/domains/base/exceptions.py`.

- A not-found exception must inherit `EntityNotFoundException`, because `BaseService.not_found_exception` is typed `type[EntityNotFoundException]`:
  ```python
  class UserNotFoundException(EntityNotFoundException):
      def __init__(self, message: str = "User not found") -> None:
          super().__init__(message)
  ```
- Other domain errors inherit `DomainException` directly, for example `InvalidCredentialsError`.
- Create one class per failure mode and override `__init__` with a domain-specific default message.
- A docstring may state the intended HTTP mapping, but the mapping belongs in `app/api/`. Never import `app/api/` or raise `HTTPException` here.
