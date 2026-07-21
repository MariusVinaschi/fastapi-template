# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Tasks run through `just` (see `Justfile`) and `uv`:

```bash
just env-init                    # cp .env.sample + .env.local.sample (once)
just install                     # uv sync
just dev                         # run API with hot reload (fastapi dev app/api/main.py)
just test                        # uv run pytest
just test-cov                    # pytest with coverage (HTML + terminal)
just lint                        # ruff check app/ tests/
just format                      # ruff format app/ tests/
just type-check                  # ty check app/  (app/scripts/ is excluded)
just migrate                     # alembic upgrade head
just migrate-create "message"    # alembic autogenerate migration
just serve-flows                 # serve Prefect flows in-process (dev, no Docker rebuild)
```

Run a single test file or test:

```bash
uv run pytest tests/users/api/test_api_get_me.py
uv run pytest tests/users/api/test_api_get_me.py -k "test_name"
```

### Tests require a real PostgreSQL

There are no database mocks. `tests/conftest.py` redirects `APP_DB_NAME` to a dedicated test database (`APP_DB_TEST_NAME`, default `fastapi_template_test`) **before any `app.*` import** — that's why its imports sit below `_apply_test_database_env()` and why `tests/conftest.py` has a ruff E402 per-file-ignore. Each test function creates and drops all tables in that test DB. Setup:

```bash
docker compose up -d dbapp
docker exec dbapp psql -U fastapitemplateuser -d fastapitemplatedb -c "CREATE DATABASE fastapi_template_test;"  # once
```

Connection comes from env vars via `app/infrastructure/config.py` (pydantic-settings loads `.env` then `.env.local`). Docker Compose reads `.env` only (`APP_DB_HOST=dbapp`); local dev overrides host in `.env.local` (`APP_DB_HOST=localhost`). CI uses `APP_DB_HOST=localhost` with a Postgres 17 service container.

### Commit convention

Conventional Commits are enforced (prek hooks + commitizen): `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`. Versioning is automated with python-semantic-release (RC on every merge to `main`, stable releases via manual workflow dispatch) — never bump `pyproject.toml:project.version` by hand.

### Code comments

Keep comments short. Only add one when the code isn't self-explanatory (a non-obvious constraint, invariant, or workaround) — don't restate what the code does.

## Architecture

DDD with strict layer separation. Business logic lives exclusively in `app/domains/` and has **zero framework dependencies** — FastAPI (`app/api/`) and Prefect (`app/workers/`) are adapters that consume the domain, never the other way around.

```
app/
├── api/            # HTTP delivery: routes, dependencies.py (DI bridge), exceptions
├── domains/        # Pure business logic (base/ abstractions + one folder per domain)
├── workers/        # Prefect flows and tasks
└── infrastructure/ # DB engine/session, Settings, security (Clerk JWT + API key), observability, middleware
```

Each domain folder (see `app/domains/users/` as the reference implementation) contains: `models.py` (SQLAlchemy ORM), `schemas.py` (Pydantic DTOs), `repository.py`, `service.py`, `exceptions.py`, `authorization.py`, `filters.py`, `factory.py` (test factories). Repositories and services compose generic CRUD mixins from `app/domains/base/repository.py` and `app/domains/base/service.py` (`List`, `Read`, `Create`, `Update`, `Delete`, `Bulk*`).

### Two-layer authorization (the core invariant)

Services are instantiated only through explicit factory methods:

- `Service.for_user(session, authorization_context)` — all API endpoints. Enforces both layers.
- `Service.for_system(session)` — background jobs, webhooks, admin scripts. Bypasses all checks (context is `None`), so its use must be deliberate and visible.

The two layers:

1. **Service — permission checks** (can the user do this?): **deny-by-default** — in user context only the actions in `_default_allowed_user_actions` (base: `read`, `list`) are allowed; anything else raises `PermissionDenied`. Whitelist actions per service or override `_check_general_permissions(action)` / `_check_instance_permissions(action, instance)`.
2. **Repository — data scoping** (what rows can the user see?): `_apply_user_scope(query)` delegates to the domain's `AuthorizationScopeStrategy.apply_scope()`, filtering at the SQL level so unauthorized rows never leave the database. `bulk_delete` scopes the incoming IDs the same way.

Rules that follow from this design:

- Custom repository methods (e.g. `find_by_email`) should call `_apply_user_scope`; if one intentionally bypasses scoping, validate permissions in the service layer.
- Never pass `None` as `authorization_context` directly — use `for_system()`.
- The FastAPI bridge is `app/api/dependencies.py`: `auth.get_current_user` → `UserAuthorizationAdapter(user)` → `AuthorizationContext` (`CurrentAuthContext` / `CurrentAdminAuthContext` annotated deps).

### Transaction boundary (Unit of Work)

Repositories **never commit** — mutations only `flush()`. The commit happens once per HTTP request in `get_session` (rollback on any exception) and once per Prefect flow in `get_prefect_db_session`. Don't add `session.commit()` inside domain code; an explicit intermediate commit is acceptable only in workers as a durable checkpoint before an external side-effect.

### Adding a new domain

1. Create `app/domains/<entity>/` with the files listed above (compose base mixins).
2. Register the models in `alembic/env.py` so autogenerate detects them, then `just migrate-create "..."`.
3. Add routes in `app/api/routes/<entity>.py` and register them in `app/api/router.py`.

### Deployment shape

One multi-stage `dockerfile` produces three images: `api` (full app), `worker` (no `app/api/`), `migrations` (runs `alembic upgrade head`). The worker image must not import from `app/api/` — keep worker code depending only on `domains/` and `infrastructure/`.
