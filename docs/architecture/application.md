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
| A new domain cannot arrive without its confinement contract | `tests/architecture/` |

The contracts live in `pyproject.toml` under `[tool.importlinter]`. Each one has a
fixture package under `tests/architecture/fixtures/` that it must reject: a contract
matching nothing is otherwise indistinguishable from a contract that is satisfied.

A deliberate exception is declared in the contract's `ignore_imports` with a reason.
Stale exceptions fail the gate rather than accumulating.

Six more invariants that no import graph can see are checked the same way, by
ast-grep rules (`rules/architecture/*.yml`) and, where a rule needs a resolved type
rather than syntax, by tests under `tests/architecture/`:

| Rule | Checked by |
| --- | --- |
| Repositories and services never commit | rule *b1-no-commit-in-domain* |
| A custom repository read applies the authorization scope, or declares a system-only bypass | rule *b2-unscoped-repository-read* |
| A domain service or repository is built only via `for_user`/`for_system` | rule *b3-direct-service-construction* |
| `authorization_context=None` never appears at a call site | rule *b4-explicit-none-authorization-context* |
| No route's response model reaches a stored credential, password, token or hash | `tests/architecture/test_no_secrets_in_responses.py` |
| Every domain's repository wires a scope strategy from its own domain | `tests/architecture/test_authorization_is_declared.py` |

**b2 is a syntactic contract, not a proof of authorization.** It checks that the
scoping ritual is present in a method body — nothing more. It cannot establish that
every execution path is correctly scoped, which needs type resolution, data flow and
call-graph analysis no rule here performs. A green b2 is never evidence that a query
is safe; authorization correctness remains a matter for review and for the
authorization tests in the existing suite.

An ast-grep exception is a comment naming the exact rule
(`# ast-grep-ignore: <rule-id>`) with the reason on the line above, immediately
before the flagged line. `just architecture-check` rejects a blanket suppression
that names no rule and a suppression that no longer matches any violation, so
neither can accumulate silently. Every rule ships `valid` and `invalid` cases run by
`ast-grep test`: a rule matching nothing is otherwise indistinguishable from a
satisfied one.

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
