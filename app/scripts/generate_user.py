import asyncio

from app.domains.users.service import UserService, APIKeyService
from app.domains.users.schemas import RoleEnum, UserCreate
from app.infrastructure.database import async_session
from app.infrastructure.config import settings

USER_EMAIL = settings.DEFAULT_USER
USER_ROLE = settings.DEFAULT_USER_ROLE


async def main():
    # Create tables first
    from app.infrastructure.database import async_engine
    from app.domains.base.models import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        user = await UserService.for_system(session).create(
            UserCreate(
                email=USER_EMAIL,
                role=RoleEnum(USER_ROLE),
                clerk_id="local_user",
            )
        )
        response = await APIKeyService.for_system(session).generate_api_key(user)
        print(f"""
            User created:
            Email: {USER_EMAIL}
            Role: {USER_ROLE}
            API Key: {response.api_key}
            """)


def cli():
    """Entry point for the console script"""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
