from collections.abc import Iterator
from typing import AsyncGenerator

import pytest
import pytest_asyncio
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


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    async_session = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
    async with async_session() as session:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()
