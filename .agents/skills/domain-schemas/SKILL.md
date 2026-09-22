---
name: domain-schemas
description: Use when creating or modifying framework-agnostic Pydantic DTOs under app/domains/**/schemas.py. Do not use for FastAPI request routing, ORM models, repositories, or services.
---

# Domain schemas

Schemas are pure, framework-agnostic Pydantic DTOs. Follow `app/domains/users/schemas.py` and the mixins in `app/domains/base/schemas.py`.

- Use separate schemas for Create input, Patch input (every field optional), Read/Response, internal persistence, and login/auth I/O such as `UserLogin` and `TokenPair`. Never reuse one schema across these concerns.
- Read schemas compose `UUIDSchema` and `TimestampSchema`; their `from_attributes=True` allows construction from ORM instances. Input-only schemas do not use that configuration.
- Response schemas never expose a stored secret: `password_hash`, `key_hash`, `token_hash`, or other server-side credential state. The token actually issued to its owner (`TokenPair` from `/auth/login` and `/auth/refresh`, a freshly generated key in `APIKeyGenerated`) is the sanctioned exception, not a violation -- it is the endpoint's entire purpose. `just architecture-check` walks every route's effective response type, including one declared `response_model=None` and resolved from its return annotation, and requires each such exception to be named explicitly.
- Prefer constrained types such as `EmailStr` and `StrEnum` over hand-written validation when the type can express the rule.
- A system-managed entity may expose only an internal-persist schema, with no Read or Patch DTO.
