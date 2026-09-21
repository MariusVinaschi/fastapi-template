"""Shared pytest bootstrap for tests/ and features/, before any app import."""

import os
from pathlib import Path

from scripts.environment import runtime_environment

os.environ.update(runtime_environment(Path(__file__).parent, testing=True))
pytest_plugins = ["scripts.pytest_workflow"]

from collections.abc import AsyncGenerator, Iterator

import pytest
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.main import create_application
from app.api.rate_limit import limiter
from app.domains.base.models import Base
from app.infrastructure.database import async_engine

# Disable SlowAPI rate limiting in tests: limits are per-IP and would leak across tests.
limiter.enabled = False

fake = Faker()


@pytest.fixture
def app() -> Iterator[FastAPI]:
    yield create_application()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def db_session(request: pytest.FixtureRequest) -> AsyncGenerator:
    if request.node.get_closest_marker("unit"):
        pytest.fail("Unit tests cannot request db_session, including through dynamic BDD steps")
    async_session = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
    async with async_session() as session:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()
