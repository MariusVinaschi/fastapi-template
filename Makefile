.PHONY: help install dev test lint format clean docker-build docker-up docker-up-registry docker-down migrate

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Development
# =============================================================================

install: ## Install dependencies with uv
	uv sync

dev: ## Run FastAPI in development mode
	uv run fastapi dev app/api/main.py 

# =============================================================================
# Testing & Quality
# =============================================================================

test: ## Run all tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linters (ruff)
	uvx ruff check app/

format: ## Format code
	uvx ruff format app/

type-check: ## Type check code
	uvx ty check app/

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	uv run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="your message")
	uv run alembic revision --autogenerate -m "$(MESSAGE)"

migrate-down: ## Rollback one migration
	uv run alembic downgrade -1

migrate-history: ## Show migration history
	uv run alembic history

# =============================================================================
# Docker
# =============================================================================

docker-build-api: ## Build API Docker image
	docker build --target api -t fastapi-template:api .

docker-build-worker: ## Build Worker Docker image (tags fastapi-template:worker and fastapi-template-worker:latest for Prefect)
	docker build --target worker -t fastapi-template:worker -t fastapi-template-worker:latest .

docker-build-migrations: ## Build Migrations Docker image
	docker build --target migrations -t fastapi-template:migrations .

docker-build-all: docker-build-api docker-build-worker docker-build-migrations ## Build all Docker images

docker-up: docker-up-app docker-up-prefect ## Start all services (app + prefect)

docker-up-app: ## Start only FastAPI app services (builds API image locally)
	docker-compose up -d

docker-up-registry: ## Start app using API image from registry (set API_IMAGE e.g. ghcr.io/org/fastapi-template:latest)
	@if [ -z "$${API_IMAGE}" ]; then echo "Error: set API_IMAGE (e.g. export API_IMAGE=ghcr.io/org/fastapi-template:latest)"; exit 1; fi
	docker-compose -f docker-compose.registry.yml up -d

docker-up-prefect: ## Start only Prefect services
	docker-compose -f docker-compose.prefect.yml up -d

docker-down: docker-down-app docker-down-prefect ## Stop all services (app + prefect)

docker-down-app: ## Stop only app services
	docker-compose down

docker-down-prefect: ## Stop only Prefect services
	docker-compose -f docker-compose.prefect.yml down

docker-logs: ## Show logs from app services (use docker-logs-app or docker-logs-prefect for specific)
	docker-compose logs -f

docker-logs-app: ## Show logs from app services
	docker-compose logs -f

docker-logs-prefect: ## Show logs from Prefect services
	docker-compose -f docker-compose.prefect.yml logs -f

docker-logs-api: ## Show API logs
	docker-compose logs -f api

docker-logs-worker: ## Show Prefect worker logs
	docker-compose logs -f prefect-worker

docker-logs-prefect-server: ## Show Prefect server logs
	docker-compose -f docker-compose.prefect.yml logs -f prefect-server prefect-services

docker-restart: docker-down docker-up ## Restart all services

docker-restart-app: docker-down-app docker-up-app ## Restart only app services

docker-restart-prefect: docker-down-prefect docker-up-prefect ## Restart only Prefect services

# =============================================================================
# Database Population
# =============================================================================

create-user: ## Create a new user
	uv run generate-user


# =============================================================================
# Setup prefect
# =============================================================================

init-prefect: ## Initialize Prefect
	uv run init-prefect

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .coverage coverage.xml

clean-docker: ## Remove all Docker images and volumes (app + prefect)
	docker-compose down -v
	docker-compose -f docker-compose.prefect.yml down -v
	docker rmi fastapi-template:api fastapi-template:worker fastapi-template:migrations 2>/dev/null || true
