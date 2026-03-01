# Justfile – FastAPI Template task runner
# Install: https://just.systems/en/latest/install/
# List commands: just --list

default:
    # Show available commands
    just --list

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------

install:
    # Install dependencies with uv
    uv sync

dev:
    # Run FastAPI in development mode
    uv run fastapi dev app/api/main.py

# -----------------------------------------------------------------------------
# Testing & Quality
# -----------------------------------------------------------------------------

prek-install:
    # Install prek git hooks (pre-commit + commit-msg for Conventional Commits)
    uv run prek install && uv run prek install --hook-type commit-msg

prek-run:
    # Run all prek hooks on the whole repo
    uv run prek run --all-files

test:
    # Run all tests
    uv run pytest

test-cov:
    # Run tests with coverage
    uv run pytest --cov=app --cov-report=html --cov-report=term

lint:
    # Run linters (ruff)
    uvx ruff check app/

format:
    # Format code
    uvx ruff format app/

type-check:
    # Type check code
    uvx ty check app/

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

migrate:
    # Run database migrations
    uv run alembic upgrade head

migrate-create message:
    # Create a new migration (usage: just migrate-create "your message")
    uv run alembic revision --autogenerate -m "{{message}}"

migrate-down:
    # Rollback one migration
    uv run alembic downgrade -1

migrate-history:
    # Show migration history
    uv run alembic history

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------

docker-build-api:
    # Build API Docker image
    docker build --target api -t fastapi-template:api .

docker-build-worker:
    # Build Worker Docker image (tags for Prefect)
    docker build --target worker -t fastapi-template:worker -t fastapi-template-worker:latest .

docker-build-migrations:
    # Build Migrations Docker image
    docker build --target migrations -t fastapi-template:migrations .

docker-build-all: docker-build-api docker-build-worker docker-build-migrations
    # Build all Docker images
    @true

docker-up: docker-up-app docker-up-prefect
    # Start all services (app + prefect)
    @true

docker-up-app:
    # Start only FastAPI app services (builds API image locally)
    docker compose up -d

docker-up-registry:
    # Start app using API image from registry (set API_IMAGE e.g. ghcr.io/org/fastapi-template:latest)
    #!/usr/bin/env bash
    if [ -z "${API_IMAGE}" ]; then
    echo "Error: set API_IMAGE in .env (e.g. API_IMAGE=ghcr.io/org/fastapi-template:latest)"
    exit 1
    fi
    docker compose -f docker-compose.registry.yml up -d

docker-up-prefect:
    # Start only Prefect services
    docker compose -f docker-compose.prefect.yml up -d

docker-down: docker-down-app docker-down-prefect
    # Stop all services (app + prefect)
    @true

docker-down-app:
    # Stop only app services
    docker compose down

docker-down-prefect:
    # Stop only Prefect services
    docker compose -f docker-compose.prefect.yml down

docker-logs:
    # Show logs from app services
    docker compose logs -f

docker-logs-app:
    # Show logs from app services
    docker compose logs -f

docker-logs-prefect:
    # Show logs from Prefect services
    docker compose -f docker-compose.prefect.yml logs -f

docker-logs-api:
    # Show API logs
    docker compose logs -f api

docker-logs-worker:
    # Show Prefect worker logs
    docker compose logs -f prefect-worker

docker-logs-prefect-server:
    # Show Prefect server logs
    docker compose -f docker-compose.prefect.yml logs -f prefect-server prefect-services

docker-restart: docker-down docker-up
    # Restart all services
    @true

docker-restart-app: docker-down-app docker-up-app
    # Restart only app services
    @true

docker-restart-prefect: docker-down-prefect docker-up-prefect
    # Restart only Prefect services
    @true

# -----------------------------------------------------------------------------
# Database Population
# -----------------------------------------------------------------------------

create-user:
    # Create a new user
    uv run generate-user

# -----------------------------------------------------------------------------
# Setup Prefect
# -----------------------------------------------------------------------------

init-prefect:
    # Initialize Prefect (blocks, work pool)
    uv run init-prefect

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------

clean:
    # Clean up cache and temporary files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name ".coverage" -delete
    rm -rf htmlcov/ .coverage coverage.xml

clean-docker:
    # Remove all Docker images and volumes (app + prefect)
    docker compose down -v
    docker compose -f docker-compose.prefect.yml down -v
    docker rmi fastapi-template:api fastapi-template:worker fastapi-template:migrations 2>/dev/null || true
