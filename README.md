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


## Environment Variables

See `.env.example` for all available configuration options.
