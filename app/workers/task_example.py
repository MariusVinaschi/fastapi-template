from prefect import flow, task
from prefect.blocks.system import Secret
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.models import User
from app.domains.users.schemas import UserCreate
from app.domains.users.service import UserService
from app.infrastructure.database import get_prefect_session


@task
def get_session() -> AsyncSession:
    db_informations = Secret.load("appdb", _sync=True).get()
    return get_prefect_session(
        db_host=db_informations["db_host"],
        db_port=db_informations["db_port"],
        db_user=db_informations["db_user"],
        db_password=db_informations["db_password"],
        db_name=db_informations["db_name"],
    )


@task
async def create_user(session: AsyncSession, email: str, role: str, clerk_id: str) -> User:
    return await UserService.for_system(session).create(
        UserCreate(
            email=email,
            role=role,
            clerk_id=clerk_id,
        )
    )


@flow(name="Example flow to create a User", log_prints=True)
async def create_user_flow():
    session = get_session()
    await create_user(session, "test@example.com", "admin", "test")
