import logging
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
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


# Prefect-specific database session
def get_prefect_session(
    db_host: str,
    db_port: int,
    db_user: str,
    db_password: str,
    db_name: str,
) -> AsyncSession:
    """
    Create a database session specifically for Prefect tasks.
    This function uses environment variables that are set by Prefect.
    """
    logger.info("Creating Prefect database session")

    # Create database URL for Prefect tasks
    db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Create engine and session for Prefect
    prefect_engine = create_async_engine(db_url, echo=False, future=True)

    prefect_session = async_sessionmaker(bind=prefect_engine, autoflush=False, expire_on_commit=False)

    return prefect_session()
