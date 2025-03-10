import asyncio

from sqlalchemy.ext.asyncio import AsyncSession


from app.database import async_session

from app.user.factory import UserFactory


async def populate_database(session: AsyncSession):
    for _ in range(10):
        await UserFactory.create_async(
            session=session,
        )


async def main():
    print("Start populate database ... ")
    async with async_session() as session:
        await populate_database(session)
    print("Finish !")


if __name__ == "__main__":
    asyncio.run(main())
