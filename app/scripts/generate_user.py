import asyncio

from app.domains.users.password import hash_password
from app.domains.users.schemas import RoleEnum, UserCreate
from app.domains.users.service import APIKeyService, UserService
from app.infrastructure.config import settings
from app.infrastructure.database import async_session

USER_EMAIL = settings.DEFAULT_USER
USER_ROLE = settings.DEFAULT_USER_ROLE
USER_PASSWORD = settings.DEFAULT_USER_PASSWORD


async def main():
    # Create tables first
    from app.domains.base.models import Base
    from app.infrastructure.database import async_engine

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        user = await UserService.for_system(session).create(
            UserCreate(
                email=USER_EMAIL,
                role=RoleEnum(USER_ROLE),
                password_hash=hash_password(USER_PASSWORD),
            )
        )
        response = await APIKeyService.for_system(session).generate_api_key(user)
        print(f"""
            User created:
            Email: {USER_EMAIL}
            Role: {USER_ROLE}
            Password: {USER_PASSWORD}
            API Key: {response.api_key}
            """)


def cli():
    """Entry point for the console script"""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
