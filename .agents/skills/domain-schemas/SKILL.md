---
name: domain-schemas
description: Use when creating or modifying framework-agnostic Pydantic DTOs under app/domains/**/schemas.py. Do not use for FastAPI request routing, ORM models, repositories, or services.
---

# Domain schemas

Schemas are pure, framework-agnostic Pydantic DTOs. Follow `app/domains/users/schemas.py` and the mixins in `app/domains/base/schemas.py`.

- Use separate schemas for Create input, Patch input (every field optional), Read/Response, internal persistence, and login/auth I/O such as `UserLogin` and `TokenPair`. Never reuse one schema across these concerns.
- Read schemas compose `UUIDSchema` and `TimestampSchema`; their `from_attributes=True` allows construction from ORM instances. Input-only schemas do not use that configuration.
- Response schemas never expose `password_hash`, access/refresh tokens, or internal auth state. A raw secret may be returned once at its generation time, as with `APIKeyGenerated`.
- Prefer constrained types such as `EmailStr` and `StrEnum` over hand-written validation when the type can express the rule.
- A system-managed entity may expose only an internal-persist schema, with no Read or Patch DTO.
