import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import logfire
from prefect_sqlalchemy.database import SqlAlchemyConnector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.config import settings

# Logfire is configured in app.api.main; we only instrument SQLAlchemy here.
logger = logging.getLogger(__name__)

async_engine = create_async_engine(str(settings.DB_URL), echo=False, future=True)
logfire.instrument_sqlalchemy(async_engine)

async_session = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)


async def get_session() -> AsyncGenerator:
    try:
        async with async_session() as session:
            yield session
    except SQLAlchemyError as e:
        logger.exception(e)


@asynccontextmanager
async def get_prefect_db_session(block_name: str):
    """Context manager to load the connector and create the session."""
    load_result = SqlAlchemyConnector.load(block_name)
    if load_result is None:
        raise ValueError(f"Prefect block {block_name!r} not found")
    connector_cm = await load_result
    if connector_cm is None:
        raise ValueError(f"Prefect block {block_name!r} failed to load")
    async with connector_cm as connector:
        engine = connector.get_engine()
        logfire.instrument_sqlalchemy(engine)
        session_factory = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
