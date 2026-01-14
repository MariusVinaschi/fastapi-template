from collections.abc import Iterator
from typing import AsyncGenerator

import pytest
from asyncpg.exceptions import InvalidCatalogNameError
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.domains.base.models import Base
from app.infrastructure.database import async_engine
from app.api.main import create_application

fake = Faker()


@pytest.fixture
def app() -> Iterator[FastAPI]:
    yield create_application()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


def create_db_if_not_exists(db_url):
    try:
        db_exists = database_exists(db_url)
    except InvalidCatalogNameError:
        db_exists = False

    if not db_exists:
        create_database(db_url)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    async_session = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
    async with async_session() as session:
        async with async_engine.begin() as conn:
            await conn.run_sync(create_db_if_not_exists, async_engine.url)
            await conn.run_sync(Base.metadata.create_all)

        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()