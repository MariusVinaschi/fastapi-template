"""
Example Prefect tasks.
Demonstrates how to create tasks that use domain services.
"""
import logging

from prefect import task

logger = logging.getLogger(__name__)


@task(name="example_task")
async def example_task(message: str) -> str:
    """
    Example task that can be used in Prefect flows.
    
    Args:
        message: Message to process
        
    Returns:
        Processed message
    """
    logger.info(f"Processing message: {message}")
    return f"Processed: {message}"

