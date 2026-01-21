import logging
from pathlib import Path
from typing import List

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.resolve()
log = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), env_file_encoding="utf-8", extra="ignore")

    VERSION: str = "1.0"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redocs"
    SECRET_KEY: str = "secret"

    # URL
    API_V1_STR: str = "/api/v1"
    ENV: str = "dev"
    RELOAD: bool = True
    CORS_ORIGINS: str = "http://localhost:3000"

    TESTING: bool = False

    # DATABASE
    APP_DB_HOST: str = "dbapp"
    APP_DB_PORT: int = 5432
    APP_DB_USER: str = "dbuser"
    APP_DB_PASSWORD: str = "dbpassword"
    APP_DB_NAME: str = "dbname"
    DB_ECHO: bool = False

    # CLERK
    CLERK_FRONTEND_API_URL: str = ""
    CLERK_ALGORITHMS: str = "RS256"
    CLERK_AZP: str = "http://localhost:3000"
    CLERK_WEBHOOK_SECRET: str = "sk_test_1234567890"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    PREFECT_DB_USER: str = "prefect"
    PREFECT_DB_PASSWORD: str = "prefect"
    PREFECT_DB_NAME: str = "prefect"
    PREFECT_DB_HOST: str = "prefectdb"
    PREFECT_DB_PORT: int = 5432
    PREFECT_API_URL: str = "http://prefect-server:4200/api"
    WORK_POOL_NAME: str = "my-docker-pool"
    WORK_QUEUE_NAME: str = "my-docker-queue"

    DEFAULT_USER: str = "fastapi@example.com"
    DEFAULT_USER_ROLE: str = "admin"

    @property
    def DB_BASE(self):
        return self.APP_DB_NAME

    @property
    def DB_URL(self) -> PostgresDsn:
        """
        Assemble Database URL from settings.

        :return: Database URL.
        """
        return PostgresDsn(
            url=(
                f"postgresql+asyncpg://{self.APP_DB_USER}:"
                f"{self.APP_DB_PASSWORD}@{self.APP_DB_HOST}:"
                f"{self.APP_DB_PORT}/{self.DB_BASE}"
            )
        )

    @property
    def DB_URL_SYNC(self) -> str:
        """
        Assemble synchronous Database URL for Alembic.

        :return: Synchronous Database URL.
        """
        return (
            f"postgresql://{self.APP_DB_USER}:{self.APP_DB_PASSWORD}"
            f"@{self.APP_DB_HOST}:{self.APP_DB_PORT}/{self.DB_BASE}"
        )

    @property
    def ALLOWED_CORS_ORIGINS(self) -> List[str]:
        """
        Transform comma separated CORS origins to list.

        :return: Allowed cors origins as list.
        """
        return self.CORS_ORIGINS.split(",")


settings = Settings()
