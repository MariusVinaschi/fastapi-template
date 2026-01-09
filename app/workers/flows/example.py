"""
Example Prefect flows.
Demonstrates how to create flows that use domain services.
"""
import logging

from prefect import flow
from prefect.blocks.system import Secret

from app.infrastructure.database import get_prefect_session
from app.domains.users.service import UserService
from app.workers.tasks.example import example_task

logger = logging.getLogger(__name__)


@flow(name="example_flow")
async def example_flow(user_email: str | None = None) -> dict:
    """
    Example flow that demonstrates domain service usage.
    
    This flow shows how to:
    1. Use the database session from infrastructure
    2. Call domain services for business logic
    3. Compose tasks together
    
    Args:
        user_email: Optional email to look up user
        
    Returns:
        Dictionary with flow results
    """
    results = {}
    
    # Execute a simple task
    task_result = await example_task("Hello from Prefect!")
    results["task_result"] = task_result
    
    # Use domain service with database session
    if user_email:
        db_informations = Secret.load("appdb", _sync=True).get()
        session = get_prefect_session(
            db_host=db_informations["db_host"],
            db_port=db_informations["db_port"],
            db_user=db_informations["db_user"],
            db_password=db_informations["db_password"],
            db_name=db_informations["db_name"],
        )
        user_service = UserService.for_system(session)
        user = await user_service.get_by_email(user_email)
        results["user_found"] = True
        results["user_email"] = user.email
        logger.info(f"Found user: {user.email}")

    return results


@flow(name="user_sync_flow")
async def user_sync_flow() -> dict:
    """
    Example flow for synchronizing users.
    
    This demonstrates a real-world use case where you might
    need to process users in batch.
    """
    async with async_session() as session:
        user_service = UserService.for_system(session)
        
        # Get all users (you might want to paginate in production)
        from app.domains.base.filters import BaseFilterParams
        users = await user_service.get_all(BaseFilterParams(limit=100))
        
        processed = 0
        for user in users:
            # Do some processing on each user
            logger.info(f"Processing user: {user.email}")
            processed += 1
        
        return {
            "total_processed": processed,
            "status": "completed"
        }

