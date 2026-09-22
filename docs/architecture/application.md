# Application architecture

The application uses DDD boundaries: `app/domains/` owns business logic,
`app/api/` adapts HTTP, `app/workers/` adapts Prefect and `app/infrastructure/`
provides settings, database sessions, AuthX configuration and observability.
Domain code must not import FastAPI or Prefect. ORM/Pydantic domain types are
intentional. Worker images omit `app/api/`, so workers must not import it.

`app/api/security.py` holds the HTTP authentication dependencies. It raises
`HTTPException` and depends on the users domain, so it is a delivery adapter and
lives with the delivery layer; `app/infrastructure/` stays below the domains.

Each domain composes generic CRUD mixins from `app/domains/base/` and normally
contains models, schemas, repository, service, exceptions, authorization,
filters and test factories. Use `users` and `sessions` as concrete examples.
For detailed file conventions, load the matching `.agents/skills/domain-*/`
skill (Codex) or `.claude/rules/domains/` rule (Claude).

## Machine-checked boundaries

`just architecture-check` decides the structural rules below. Do not re-verify them
by reading code, and do not restate them as prose to be trusted:

| Rule | Checked by |
| --- | --- |
| Domains import no FastAPI, Starlette or Prefect | contract *Domains are framework-agnostic* |
| Workers import no `app/api/` | contract *Workers never import the HTTP API* |
| Delivery above domains above infrastructure; `users` below `sessions` | contract *Application layers* |
| A domain's repository is private to that domain | one *private to its domain* contract per domain |

The contracts live in `pyproject.toml` under `[tool.importlinter]` and are executed
directly by `lint-imports`.

A deliberate exception is declared in the contract's `ignore_imports` with a reason.
Stale exceptions fail the gate rather than accumulating.

Four more invariants that no import graph can see are checked by ast-grep rules
under `rules/architecture/`:

| Rule | Checked by |
| --- | --- |
| Repositories and services never commit | rule *no-commit-in-domain* |
| A custom repository read applies the authorization scope, or declares a system-only bypass | rule *unscoped-repository-read* |
| A domain service or repository is built only via `for_user`/`for_system` | rule *direct-service-construction* |
| `authorization_context=None` never appears at a call site | rule *explicit-none-authorization-context* |

**b2 and b3 are syntactic contracts.** b2 checks literal `select(...)` calls; b3
checks direct callees whose names end in `Service` or `Repository`. They do not
resolve aliases, types, data flow or call graphs. A green result is not evidence that
authorization or construction is semantically correct; those remain review and
application-test concerns.

An ast-grep exception is a comment naming the exact rule
(`# ast-grep-ignore: <rule-id>`) with the reason on the line above, immediately
before the flagged line — not the statement that contains it. Reflowing that line
(e.g. joining it with the one above) silently detaches the suppression, which then
fails as unused rather than as the original violation; keep the comment adjacent to
the exact line a rule reports. `just architecture-check` rejects a blanket
suppression that names no rule and a suppression that no longer matches any
violation, so neither can accumulate silently.

Response schema safety, repository strategy wiring, and authorization correctness
remain matters for focused application tests and review. They require semantic or
runtime knowledge and are deliberately not approximated by this structural gate.

## Authorization

API services use `Service.for_user(session, authorization_context)`.
Background work deliberately uses `Service.for_system(session)`, never a
direct None authorization context. Service permission checks are deny-by-default:
the base permits read/list only; other actions require a whitelist or explicit
general/instance permission checks.

Repositories apply an AuthorizationScopeStrategy at SQL level. Custom queries
must call `_apply_user_scope`; deliberate bypasses need service permission
checks. Bulk deletion also scopes incoming IDs. The HTTP bridge converts the
authenticated user via UserAuthorizationAdapter to AuthorizationContext.

## Transactions and schema changes

Repositories flush, never commit. `get_session` commits once per successful
HTTP request and rolls back exceptions. `get_prefect_db_session` supplies the
flow boundary. Workers may checkpoint explicitly before external side effects;
domain services may not commit.

Register new models in `alembic/env.py`, generate a migration via
`just migrate-create`, then register routes in `app/api/router.py`.
The multi-stage dockerfile builds API, worker and migration images.
