---
paths:
  - "app/domains/**/schemas.py"
---

# Schema rules

Pure Pydantic DTOs, framework-agnostic. Reference: `app/domains/users/schemas.py`, base
mixins in `app/domains/base/schemas.py`.

## One schema per concern

Never reuse a single schema across concerns. Separate:
- **Create** — input for creation
- **Patch** — partial update, all fields `Optional`.
- **Read / Response** — what's returned.
- **Internal-persist** — service-only DTO.
- **Login / auth I/O** — `UserLogin`, `TokenPair`.

## Rules

- Read schemas compose the base mixins (`UUIDSchema`, `TimestampSchema`) and thus set
  `from_attributes=True` so they build from an ORM instance. Input-only schemas don't.
- **Response schemas must never carry secrets** — no `password_hash`, no access/refresh
  tokens, no internal auth state. A raw secret is returned exactly once, at generation
  time (`APIKeyGenerated`).
- Use constrained Pydantic types (`EmailStr`, `StrEnum`) instead of hand-written
  validation where the type can express the rule.
- A system-managed entity may need only an internal-persist schema (no Read/Patch).
