"""
Pytest loads this module before test files. We point the app at a dedicated test DB
before any `app.*` import so `Settings()` and `async_engine` use the correct URL.

- Default DB name: APP_DB_TEST_NAME or "fastapi_template_test". Create it once:
    CREATE DATABASE fastapi_template_test;
"""

import os


def _apply_test_database_env() -> None:
    # Accept values like "/fastapi_template_test" from CI env parsing and normalize.
    test_db = os.environ.get("APP_DB_TEST_NAME", "fastapi_template_test").lstrip("/") or "fastapi_template_test"
    os.environ["APP_DB_TEST_NAME"] = test_db
    os.environ["APP_DB_NAME"] = test_db


def _apply_test_secrets_env() -> None:
    # SECRET_KEY and CLERK_WEBHOOK_SECRET have no defaults in Settings (fail-fast in
    # production). Tests provide throwaway values so Settings() can be instantiated
    # without a .env file (e.g. in CI). setdefault keeps any explicitly set value.
    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
    # Svix-format secret ("whsec_" + base64), required by webhook signature verification.
    os.environ.setdefault("CLERK_WEBHOOK_SECRET", "whsec_dGVzdC1jbGVyay13ZWJob29rLXNlY3JldA==")


_apply_test_database_env()
_apply_test_secrets_env()

from collections.abc import Iterator
from typing import AsyncGenerator

import pytest
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.main import create_application
from app.domains.base.models import Base
from app.infrastructure.database import async_engine

fake = Faker()


@pytest.fixture
def app() -> Iterator[FastAPI]:
    yield create_application()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    async_session = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
    async with async_session() as session:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()
