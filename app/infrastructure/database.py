import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from prefect_sqlalchemy.database import SqlAlchemyConnector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)

async_engine = create_async_engine(str(settings.DB_URL), echo=False, future=True)

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
    async with await SqlAlchemyConnector.load(block_name) as connector:
        engine = connector.get_engine()
        session_factory = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
