"""
Base factory - For testing and seeding data.
Framework agnostic factory_boy base class.
"""

from factory import Factory
from sqlalchemy.ext.asyncio import AsyncSession


class BaseFactory(Factory):
    """Base factory with async support for SQLAlchemy models"""

    @classmethod
    async def create_async(cls, **kwargs):
        """Create and persist an instance asynchronously"""
        session = kwargs.pop("session", None)
        instance = cls.build(**kwargs)
        if session and isinstance(session, AsyncSession):
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
        return instance

    @classmethod
    async def create_batch_async(cls, size, **kwargs):
        """Create multiple instances asynchronously"""
        return [await cls.create_async(**kwargs) for _ in range(size)]
