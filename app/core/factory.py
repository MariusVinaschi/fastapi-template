from factory import Factory
from sqlalchemy.ext.asyncio import AsyncSession


class BaseFactory(Factory):
    @classmethod
    async def create_async(cls, **kwargs):
        session = kwargs.pop("session", None)
        instance = cls.build(**kwargs)
        if session and isinstance(session, AsyncSession):
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
        return instance

    @classmethod
    async def create_batch_async(cls, size, **kwargs):
        return [await cls.create_async(**kwargs) for _ in range(size)]
