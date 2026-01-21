# Domain layer - Pure business logic
# This layer contains all business rules, models, repositories and services
# It has ZERO dependencies on FastAPI, Prefect, or any delivery framework

from app.domains.base.models import Base

__all__ = ["Base"]
