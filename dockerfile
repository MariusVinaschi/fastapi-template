# =============================================================================
# Base stage - Common configuration
# =============================================================================
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

# =============================================================================
# Worker stage 
# =============================================================================
FROM base AS worker

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# We do NOT copy the 'app/api' folder here.
COPY ./app/domains /app/app/domains
COPY ./app/infrastructure /app/app/infrastructure
COPY ./app/workers /app/app/workers
COPY ./app/scripts /app/scripts

# No specific CMD, Prefect will inject the run command 

# =============================================================================
# API stage - Focus on FastAPI
# =============================================================================
FROM base AS api

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# The API needs everything
COPY ./app /app/app
COPY ./alembic.ini /app/

RUN mkdir -p /app/logs
RUN touch /app/logs/app.log

EXPOSE 80
CMD ["fastapi", "run", "--workers", "4", "--port", "80", "--host", "0.0.0.0", "app/api/main.py"]

# =============================================================================
# Migrations stage - Database migrations
# =============================================================================
FROM base AS migrations

LABEL role="migrations"

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Migrations need models (domains) and alembic config
COPY ./app /app/app
COPY ./alembic.ini /app/
COPY ./alembic /app/alembic

# We define a CMD to run migrations
CMD ["alembic", "upgrade", "head"]