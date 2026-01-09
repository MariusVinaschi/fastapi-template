import asyncio

from app.user.service import UserService, APIKeyService
from app.user.schemas import UserCreate
from app.database import async_session
from app.config import settings

USER_EMAIL = settings.DEFAULT_USER
USER_ROLE = settings.DEFAULT_USER_ROLE


async def main():
    # Create tables first
    from app.database import async_engine
    from app.core.models import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        user = await UserService.for_system(session).create(
            UserCreate(email=USER_EMAIL, role=USER_ROLE)
        )
        api_key_service = APIKeyService(session)
        response = await api_key_service.generate_api_key(user)
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
