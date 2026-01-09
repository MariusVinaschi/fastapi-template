.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate

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
	fastapi dev app/api/main.py

worker: ## Run Prefect worker locally
	python -m app.workers.main

# =============================================================================
# Testing & Quality
# =============================================================================

test: ## Run all tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linters (ruff)
	ruff check app/

format: ## Format code
	ruff format app/

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="your message")
	alembic revision --autogenerate -m "$(MESSAGE)"

migrate-down: ## Rollback one migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

# =============================================================================
# Docker
# =============================================================================

docker-build-api: ## Build API Docker image
	docker build --target api -t fastapi-template:api .

docker-build-worker: ## Build Worker Docker image
	docker build --target worker -t fastapi-template:worker .

docker-build-migrations: ## Build Migrations Docker image
	docker build --target migrations -t fastapi-template:migrations .

docker-build-all: docker-build-api docker-build-worker docker-build-migrations ## Build all Docker images

docker-up: ## Start all services with docker-compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-logs-api: ## Show API logs
	docker-compose logs -f api

docker-logs-worker: ## Show Worker logs
	docker-compose logs -f worker

docker-restart: docker-down docker-up ## Restart all services

# =============================================================================
# Database Population
# =============================================================================

populate: ## Populate database with test data
	python scripts/populate_database.py

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

clean-docker: ## Remove all Docker images and volumes
	docker-compose down -v
	docker rmi fastapi-template:api fastapi-template:worker fastapi-template:migrations 2>/dev/null || true
