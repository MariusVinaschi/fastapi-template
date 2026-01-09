# Workers layer - Prefect flows and tasks
# This is the Prefect-specific adapter that consumes the domain layer
# All async processing and background jobs are defined here

from app.workers.tasks import example_task

__all__ = ["example_task"]

