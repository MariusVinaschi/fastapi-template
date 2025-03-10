import logging
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

async_engine = create_async_engine(settings.DB_URL, echo=False, future=True)

async_session = async_sessionmaker(
    bind=async_engine, autoflush=False, expire_on_commit=False
)


async def get_session() -> AsyncGenerator:
    try:
        async with async_session() as session:
            yield session
    except SQLAlchemyError as e:
        logger.exception(e)
