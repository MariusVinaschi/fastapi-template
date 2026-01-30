from prefect import flow, task

from app.domains.users.models import User
from app.domains.users.schemas import UserCreate
from app.domains.users.service import UserService
from app.infrastructure.database import get_prefect_db_session


@task
async def create_user(email: str, role: str, clerk_id: str) -> User:
    async with get_prefect_db_session("dbapp-sqlalchemy") as session:
        return await UserService.for_system(session).create(
            UserCreate(
                email=email,
                role=role,
                clerk_id=clerk_id,
            )
        )


@flow(name="Example flow to create a User", log_prints=True)
async def create_user_flow():
    await create_user("test@example.com", "admin", "test")


if __name__ == "__main__":
    create_user_flow.serve("exemple-flow")
