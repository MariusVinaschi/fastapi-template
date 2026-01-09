"""
Prefect tasks module.
Contains reusable tasks that can be composed into flows.
"""
from app.workers.tasks.example import example_task

__all__ = ["example_task"]

