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

### 4. Authorization Architecture

This template implements a **two-layer defense-in-depth authorization system** that separates **permissions** (what actions are allowed) from **data scoping** (what data is visible).

#### Overview

The authorization system operates at two independent layers:

1. **Service Layer** (`_check_*_permissions`): Validates **whether** a user can perform an action
2. **Repository Layer** (`_apply_user_scope`): Filters **which** data the user can see

This separation ensures that a bug in one layer doesn't compromise the other, following security best practices.

#### Architecture Flow

```
API Route
  ↓
Service (for_user/for_system)
  ↓
  ├─→ Permission Checks (CAN the user DO this?)
  │   ├─→ _check_general_permissions(action)
  │   └─→ _check_instance_permissions(action, instance)
  │
  └─→ Repository Operations
      ↓
      └─→ Scope Filtering (WHAT data can the user SEE?)
          └─→ _apply_user_scope(query)
              ├─→ context is None? → return unfiltered query (system)
              └─→ context exists? → scope_strategy.apply_scope(query, context)
```

#### Key Components

**1. AuthorizationContext** (`app/domains/base/authorization.py`)

Abstract interface that provides user information:

```python
class AuthorizationContext(ABC):
    @property
    @abstractmethod
    def user_id(self) -> str: ...
    
    @property
    @abstractmethod
    def user_email(self) -> str: ...
    
    @property
    @abstractmethod
    def user_role(self) -> str: ...
```

**2. AuthorizationScopeStrategy** (`app/domains/base/authorization.py`)

Defines **how** to filter queries based on user context. Each domain implements its own strategy:

```python
class AuthorizationScopeStrategy(ABC, Generic[T]):
    @abstractmethod
    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        """Filter query results based on user context"""
        ...
```

**Example Implementation** (`app/domains/users/authorization.py`):

```python
class APIKeyScopeStrategy(AuthorizationScopeStrategy):
    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        # Only show API keys owned by the user
        return query.where(self.model.user_id == context.user_id)
```

**3. Repository Layer** (`app/domains/base/repository.py`)

The repository is the **guardian** that decides **IF** scope should be applied:

```python
def _apply_user_scope(self, query: Select) -> Select:
    """Apply user scope using the repository's authorization context"""
    if self.authorization_context is None:
        return query  # System operation: no filtering
    
    return self.scope_strategy.apply_scope(query, self.authorization_context)
```

**Important**: The repository handles the `None` check **before** calling `apply_scope`. The scope strategy **never** receives `None` - it only decides **how** to filter when a user context exists.

**4. Service Layer** (`app/domains/base/service.py`)

The service validates **permissions** before delegating to the repository:

```python
def _check_general_permissions(self, action: str) -> bool:
    """Check if user can perform this action type"""
    if self._is_system_operation():
        return True  # System operations bypass checks
    
    # Override in subclasses for domain-specific logic
    return True

def _check_instance_permissions(self, action: str, instance: ModelType) -> bool:
    """Check if user can perform this action on this specific instance"""
    if self._is_system_operation():
        return True
    
    # Override in subclasses for domain-specific logic
    return True
```

#### Factory Methods: Explicit System vs User Operations

Services provide two factory methods that make the authorization mode explicit:

```python
# User operation: with authorization context
service = UserService.for_user(session, authorization_context)

# System operation: bypasses all checks (use with caution!)
service = UserService.for_system(session)
```

**When to use `for_system()`:**
- Background jobs / workers
- Webhook handlers (e.g., Clerk user sync)
- Admin scripts
- Internal system operations

**When to use `for_user()`:**
- All API endpoints handling user requests
- Any operation triggered by an authenticated user

#### Security Guarantees

1. **Defense in Depth**: Both service permissions and repository scoping must be bypassed for unauthorized access
2. **Query-Level Filtering**: Data filtering happens at the SQL query level - unauthorized data never leaves the database
3. **Explicit System Mode**: `for_system()` makes privileged operations visible in code reviews
4. **Type Safety**: Type checker enforces that scope strategies receive non-None contexts

#### Adding Authorization to a New Domain

1. **Create Scope Strategy** (`app/domains/myentity/authorization.py`):

```python
from app.domains.base.authorization import AuthorizationScopeStrategy, AuthorizationContext
from sqlalchemy import Select

class MyEntityScopeStrategy(AuthorizationScopeStrategy):
    def __init__(self):
        super().__init__(MyEntity)
    
    def apply_scope(self, query: Select, context: AuthorizationContext) -> Select:
        # Example: filter by owner
        return query.where(self.model.owner_id == context.user_id)
```

2. **Register in Repository** (`app/domains/myentity/repository.py`):

```python
class MyEntityRepository(ListRepositoryMixin, ...):
    def __init__(self, session: AsyncSession, authorization_context=None):
        super().__init__(
            session, 
            MyEntityScopeStrategy(),  # Pass strategy here
            MyEntity, 
            authorization_context
        )
```

3. **Override Permission Checks** (`app/domains/myentity/service.py`):

```python
class MyEntityService(BaseService):
    def _check_general_permissions(self, action: str) -> bool:
        if self._is_system_operation():
            return True
        
        # Add your permission logic here
        if action == "delete" and self.authorization_context.user_role != "admin":
            raise PermissionDenied("Only admins can delete")
        
        return True
    
    def _check_instance_permissions(self, action: str, instance: MyEntity) -> bool:
        if self._is_system_operation():
            return True
        
        # Add your instance-level checks here
        if action == "update" and instance.owner_id != self.authorization_context.user_id:
            raise PermissionDenied("Can only update own entities")
        
        return True
```

#### Important Notes

- **Custom Repository Methods**: Methods like `find_by_email()` that bypass `_apply_user_scope` **must** have their permissions checked in the service layer after fetching
- **System Operations**: Always use `for_system()` explicitly - never pass `None` as `authorization_context` to constructors directly
- **Scope Strategy Contract**: `apply_scope` always receives a non-None `AuthorizationContext` - the repository handles the None check before calling it

### 5. Single Docker Image, Multiple Roles

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
