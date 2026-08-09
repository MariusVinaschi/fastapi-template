---
paths:
  - "app/domains/**/*.py"
---

# Domain rules — cross-cutting invariants

You are editing a file under `app/domains/`. This is a **framework-agnostic DDD layer**.
Per-file rules load alongside this one (`service.md`, `repository.py` → `repository.md`,
etc.). These invariants span every domain file — apply them everywhere.

## 1. Framework-agnostic

No FastAPI / HTTP / Prefect imports anywhere in `app/domains/`. The only outward contract
is **domain exceptions** — the delivery layer (`app/api/`) catches them and maps to HTTP.

## 2. Stay inside the domain (DDD boundary)

A domain must not reach into another domain's **repository**.

- DON'T import or call `other_domain.repository.OtherRepository` from your service/repository.
- DO go through the other domain's **service**, built on the same session and context:
  `OtherService.for_user(self.session, self.authorization_context)`.
- Within a domain, the service owns the repository — nothing else instantiates it.

## 3. `for_user` vs `for_system`

Services are constructed only via the factory methods, never the raw constructor.

- User-context flow (any request-driven work): `Service.for_user(session, ctx)`.
- `Service.for_system(session)` is **only** for genuine system work — workers, webhooks,
  admin scripts — where there is no user. It bypasses all permission and scope checks, so
  its use must be deliberate and rare.
- Never reach for `for_system()` to sidestep a check when a user context exists.
- Never pass `None` as `authorization_context` directly — use `for_system()`.

## 4. Reuse base methods first

Before writing a custom method, check `app/domains/base/service.py` and
`base/repository.py`. The generic CRUD/Bulk mixins (`List`, `Read`, `Create`, `Update`,
`Delete`, `Bulk*`) already cover most needs. Add a custom method only when the behavior
genuinely isn't expressible with them — and when you do, follow the same permission +
scoping rituals the base methods use.

## 5. Always define authorization

Every entity gets an `AuthorizationScopeStrategy` (repository-level data scoping) and the
service must enforce permissions (deny-by-default). Never ship a domain without both.
See `authorization.md` and `service.md`.

## 6. Unit of Work

Repositories `flush()` / `refresh()` — **never `commit()`**. The transaction boundary is
owned by the caller: once per HTTP request in `get_session`, once per Prefect flow.

---
Reference implementation: `app/domains/users/`. Base abstractions: `app/domains/base/`.
