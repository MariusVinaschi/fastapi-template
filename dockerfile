# Multi-stage Dockerfile for FastAPI API and Prefect Workers
# Build with: docker build --target api -t myapp:api .
#             docker build --target worker -t myapp:worker .

# =============================================================================
# Base stage - Common dependencies and setup
# =============================================================================
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy application configuration
COPY ./pyproject.toml ./uv.lock ./alembic.ini /app/
COPY ./scripts /app/scripts

# Copy application code
COPY ./app /app/app

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync


# =============================================================================
# API stage - FastAPI HTTP server
# =============================================================================
FROM base AS api

LABEL role="api"
LABEL description="FastAPI HTTP server"

# Expose HTTP port
EXPOSE 80

# Health check for the API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost/api/v1/health/', timeout=5)" || exit 1

# Run FastAPI with multiple workers
CMD ["fastapi", "run", "--workers", "4", "--port", "80", "--host", "0.0.0.0", "app/api/main.py"]


# =============================================================================
# Worker stage - Prefect task execution
# =============================================================================
FROM base AS worker

LABEL role="worker"
LABEL description="Prefect worker for async tasks"

# Workers don't need exposed ports typically
# Add if your worker needs to expose metrics or health endpoints

# Run Prefect flows/tasks
CMD ["python", "-m", "app.workers.main"]


# =============================================================================
# Migrations stage - Database migrations (optional, for CI/CD)
# =============================================================================
FROM base AS migrations

LABEL role="migrations"
LABEL description="Database migration runner"

# Copy migrations directory
COPY ./migrations /app/migrations

# Run Alembic migrations
CMD ["alembic", "upgrade", "head"]
