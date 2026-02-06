# FastAPI Template - Domain-Driven Design

A production-ready FastAPI template following Domain-Driven Design (DDD) principles.

## Architecture Principles

### 1. Domain-First Architecture

The core business logic lives in `app/domains/` and is **framework-agnostic**.

**Rules:**
- `app/domains/` contains models (ORM), repositories, schemas, and services
- Domain code has **ZERO dependencies** on FastAPI, Prefect, or any framework
- FastAPI and Prefect are adapters that consume the domain
- All business rules and calculations belong in domain services

**Domain Structure:**
```
app/domains/
├── base/                   # Base abstractions (shared across domains)
│   ├── authorization.py    # AuthorizationContext, ScopeStrategy
│   ├── exceptions.py       # Domain exceptions
│   ├── factory.py          # Test factory base class
│   ├── filters.py          # Filter parameters
│   ├── models.py           # Base ORM model, mixins
│   ├── repository.py       # Base repository with CRUD mixins
│   ├── schemas.py          # Base Pydantic schemas
│   └── service.py          # Base service with business logic mixins
└── users/                  # User domain
    ├── authorization.py    # User-specific scope strategies
    ├── exceptions.py       # User domain exceptions
    ├── factory.py          # User test factories
    ├── models.py           # User, APIKey ORM models
    ├── repository.py       # UserRepository, APIKeyRepository
    ├── schemas.py          # User DTOs
    └── service.py          # UserService, APIKeyService
```

### 2. Separation of Concerns

```
app/
├── api/                    # FastAPI routes only (HTTP delivery layer)
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── exceptions.py       # HTTP exceptions
│   ├── main.py             # FastAPI app factory
│   ├── router.py           # Route aggregation
│   └── routes/             # Route handlers
│       ├── health.py
│       ├── users.py
│       └── webhooks/
│           └── clerk.py
├── workers/                # Prefect flows/tasks only (async processing)
│   ├── flows/              # Prefect flow definitions
│   │   └── example.py
│   ├── tasks/              # Reusable Prefect tasks
│   │   └── example.py
│   └── main.py             # Worker entry point
├── domains/                # Pure business logic (see above)
├── infrastructure/         # DB, settings, external APIs
│   ├── config.py           # Application settings
│   ├── database.py         # SQLAlchemy engine/session
│   └── security.py         # Authentication (Clerk JWT, API keys)
```

### 3. Adding a New Domain

1. Create the domain folder: `app/domains/myentity/`
2. Add the files:
   - `models.py` - ORM models
   - `schemas.py` - Pydantic DTOs
   - `repository.py` - Data access layer
   - `service.py` - Business logic
   - `exceptions.py` - Domain exceptions
   - `authorization.py` - Scope strategies (if needed)
3. Register models in `app/models.py` and `migrations/env.py`
4. Create API routes in `app/api/routes/`
5. (Optional) Create Prefect tasks/flows in `app/workers/`

### 4. Single Docker Image, Multiple Roles

One repository, **one multi-stage Dockerfile**, multiple images:

```bash
# Build different images from the same Dockerfile
docker build --target api -t myapp:api .
docker build --target worker -t myapp:worker .
docker build --target migrations -t myapp:migrations .

# Run them separately
docker run -p 8000:80 myapp:api
docker run myapp:worker
```

## Quick Start

### Prerequisites

- Python 3.13+
- Docker & Docker Compose
- uv (Python package manager)

### Development Setup (Local)

```bash
# Install dependencies
make install

# Start infrastructure (database)
docker-compose up -d dbapp

# Run migrations
make migrate

# Start the API server
make dev

# In another terminal, start worker (optional)
make worker
```

**Using Prefect locally**: For the worker or scripts (e.g. `make init-prefect`) to contact the Prefect server, export the auth (align with `PREFECT_LOGIN_USER` and `PREFECT_LOGIN_PASSWORD` in your `.env`):

```bash
export PREFECT_API_URL="http://0.0.0.0:4200/api"
export PREFECT_API_AUTH_STRING="admin:pass"
# or with .env credentials: export PREFECT_API_AUTH_STRING="${PREFECT_LOGIN_USER}:${PREFECT_LOGIN_PASSWORD}"
```

Start Prefect services first: `make docker-up-prefect`, then run the worker with `make worker`.

### Docker Deployment

```bash
# Build all images
make docker-build-all

# Start all services (db, migrations, api, worker)
make docker-up

# View logs
make docker-logs

# Stop everything
make docker-down
```

## Make Commands

### Development

| Command | Description |
|---------|-------------|
| `make help` | Show available commands help |
| `make install` | Install dependencies with uv |
| `make dev` | Run FastAPI in development mode |

### Testing & Quality

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage report (HTML + terminal) |
| `make lint` | Run linter (ruff) on `app/` |
| `make format` | Format code with ruff |
| `make type-check` | Type check with ty |

### Database

| Command | Description |
|---------|-------------|
| `make migrate` | Apply migrations (alembic upgrade head) |
| `make migrate-create MESSAGE="description"` | Create a new autogenerated migration |
| `make migrate-down` | Roll back the last migration |
| `make migrate-history` | Show migration history |

### Users & Prefect

| Command | Description |
|---------|-------------|
| `make create-user` | Create a new user (generate-user script) |
| `make init-prefect` | Initialize Prefect (blocks, work pool). Requires `PREFECT_API_AUTH_STRING` if the server is secured. |

### Cleanup

| Command | Description |
|---------|-------------|
| `make clean` | Remove caches (__pycache__, .pytest_cache, .ruff_cache, .coverage, htmlcov, etc.) |
| `make clean-docker` | Remove Docker images and volumes (app + Prefect) |

## Versioning & Releases

This project uses an automated versioning workflow with Release Candidates (RC).

### How It Works

```
Push to main  →  0.1.1-rc.1 (automatic)
Push to main  →  0.1.1-rc.2 (automatic)
Push to main  →  0.1.1-rc.3 (automatic)

Manual release (patch)  →  0.1.1 + tag v0.1.1
Push to main  →  0.1.2-rc.1 (new cycle)

Manual release (minor)  →  0.2.0 + tag v0.2.0
Push to main  →  0.2.1-rc.1 (new cycle)

Manual release (major)  →  1.0.0 + tag v1.0.0
```

### Creating a Stable Release

1. Go to **GitHub Actions** → **Release**
2. Click **Run workflow**
3. Choose release type:

| Type | Example | When to use |
|------|---------|-------------|
| `patch` | 1.2.3 → 1.2.4 | Bug fixes, small improvements |
| `minor` | 1.2.3 → 1.3.0 | New features, backward compatible |
| `major` | 1.2.3 → 2.0.0 | Breaking changes |

### Commit Style (Recommended)

While commits don't affect versioning, we recommend using clear prefixes for readability:

```bash
feat: add user dashboard
fix: resolve login timeout issue
docs: update API documentation
refactor: simplify auth middleware
test: add integration tests for users
chore: update dependencies
```

## Environment Variables

See `.env.sample` for all available configuration options.
