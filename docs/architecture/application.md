# Application architecture

The application uses DDD boundaries: `app/domains/` owns business logic,
`app/api/` adapts HTTP, `app/workers/` adapts Prefect and `app/infrastructure/`
provides settings, database sessions, AuthX JWT/API keys and observability.
Domain code must not import FastAPI or Prefect. ORM/Pydantic domain types are
intentional. Worker images omit `app/api/`, so workers must not import it.

Each domain composes generic CRUD mixins from `app/domains/base/` and normally
contains models, schemas, repository, service, exceptions, authorization,
filters and test factories. Use `users` and `sessions` as concrete examples.
For detailed file conventions, load the matching `.agents/skills/domain-*/`
skill (Codex) or `.claude/rules/domains/` rule (Claude).

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
