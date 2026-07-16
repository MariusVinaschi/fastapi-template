import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import HTTPException
from prefect_sqlalchemy.database import SqlAlchemyConnector
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)

async_engine = create_async_engine(str(settings.DB_URL), echo=False, future=True)

async_session = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Request-scoped transaction boundary for FastAPI handlers.

    Commits once on success, rolls back on any unhandled exception.
    This replaces the legacy per-mutation commits that lived in repository mixins
    and makes the HTTP request the single, explicit Unit of Work.
    """
    async with async_session() as session:
        try:
            yield session
        except HTTPException:
            logger.debug("HTTP exception during request; rolling back DB session")
            await session.rollback()
            raise
        except Exception:
            logger.exception("Unhandled exception during request; rolling back DB session")
            await session.rollback()
            raise
        else:
            await session.commit()


@asynccontextmanager
async def get_prefect_db_session(block_name: str):
    """Flow/task-scoped transaction boundary for Prefect workers.

    Same contract as get_session: commit on success, rollback on exception.
    Workers can still issue an explicit intermediate commit when a durable
    checkpoint is required before an external side-effect (e.g. Slack).
    """
    load_result = SqlAlchemyConnector.load(block_name)
    if load_result is None:
        raise ValueError(f"Prefect block {block_name!r} not found")
    connector_cm = await load_result
    if connector_cm is None:
        raise ValueError(f"Prefect block {block_name!r} failed to load")
    async with connector_cm as connector:
        engine = connector.get_engine()
        session_factory = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        session = session_factory()
        try:
            try:
                yield session
            except HTTPException:
                logger.debug("HTTP exception in Prefect session; rolling back")
                await session.rollback()
                raise
            except Exception:
                logger.exception("Unhandled exception in Prefect session; rolling back")
                await session.rollback()
                raise
            else:
                await session.commit()
        finally:
            await session.close()
