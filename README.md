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

### 3. Single Docker Image, Multiple Roles

One repository, **one multi-stage Dockerfile**, multiple optimized images:

```bash
# Build different images from the same Dockerfile
docker build --target api -t myapp:api .
docker build --target worker -t myapp:worker .
docker build --target migrations -t myapp:migrations .

# Run them separately
docker run -p 8000:80 myapp:api
docker run myapp:worker
```

Each stage is optimized for its specific role. See [DOCKER.md](DOCKER.md) for details.

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

### Using Makefile commands

```bash
make help                  # Show all available commands
make test                  # Run tests
make test-cov             # Run tests with coverage
make lint                 # Run linters
make format               # Format code
make migrate-create       # Create new migration
make populate             # Populate database with test data
```

## Adding a New Domain

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

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific domain tests
pytest tests/users/
```

## Environment Variables

See `.env.example` for all available configuration options.



[project]
name = "fastapi-template"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "alembic>=1.16.4",
    "argon2-cffi>=25.1.0",
    "factory-boy>=3.3.3",
    "faker>=37.4.2",
    "fastapi[standard]>=0.116.1",
    "httpx>=0.28.1",
    "prefect>=3.4.10",
    "pydantic-settings>=2.10.1",
    "psycopg2-binary>=2.9.9",
    "pyjwt>=2.10.1",
    "pytest>=8.4.1",
    "pytest-asyncio>=1.1.0",
    "pytest-mock>=3.14.1",
    "sqlalchemy>=2.0.41",
    "sqlalchemy-utils>=0.41.2",
    "prefect-sqlalchemy>=0.5.3",
    "inflection>=0.5.1",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
pythonpath = ["."]

[tool.uv]
package = true

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.setuptools]
packages = ["app"]

[tool.setuptools.package-data]
"*" = ["*.py", "*.graphql"]

[project.scripts]
generate-user = "app.scripts.generate_user:cli"
