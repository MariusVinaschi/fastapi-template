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
- **Response schemas must never carry a stored secret** — no `password_hash`, no
  `key_hash`, no `token_hash`, no other server-side credential state. The token
  actually issued to its own owner (`TokenPair` from `/auth/login` and
  `/auth/refresh`, a freshly generated key in `APIKeyGenerated`) is the sanctioned
  exception, not a violation of this rule: it is the endpoint's entire purpose, not
  leaked internal state.
  Machine-checked by `just architecture-check`: every route's effective response
  type — including one declared `response_model=None`, resolved from its return
  annotation — is walked for a credential/password/token/hash-shaped field. Each
  sanctioned exception is named explicitly, not a blanket allowance for the schema.
- Use constrained Pydantic types (`EmailStr`, `StrEnum`) instead of hand-written
  validation where the type can express the rule.
- A system-managed entity may need only an internal-persist schema (no Read/Patch).
