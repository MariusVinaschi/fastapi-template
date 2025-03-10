import logging
from pathlib import Path
from sys import modules

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.resolve()
log = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    """Application Settings"""

    model_config = SettingsConfigDict(
        env_file=f"{BASE_DIR}/.env", env_file_encoding="utf-8"
    )

    VERSION: str = "1.0"
    DOCS_URL: str = "/api/docs/"
    REDOC_URL: str = "/api/redocs"

    # URL
    API_V1_STR: str = "/api/v1"
    ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = f"http://{HOST}:{PORT}"
    RELOAD: bool = True

    TESTING: bool = False

    # DATABASE
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "fastapitemplateuser"
    DB_PASS: str = "fastapitemplatepassword"
    DB_NAME: str = "fastapitemplatedb"
    DB_ECHO: bool = False

    # AUTH0
    AUTH0_DOMAIN: str = ""
    AUTH0_API_AUDIENCE: str = ""
    AUTH0_ISSUER: str = ""
    AUTH0_ALGORITHMS: str = ""

    # EMAIL
    # MAIL_USERNAME: str = ""
    # MAIL_PASSWORD: str = ""
    # MAIL_FROM: str = ""
    # MAIL_PORT: int = 587
    # MAIL_SERVER: str = ""
    # MAIL_FROM_NAME: str = ""
    # MAIL_TLS: bool = True
    # MAIL_SSL: bool = True
    # USE_CREDENTIALS: bool = True
    # TEMPLATE_FOLDER: str = "path"

    # S3
    S3_ACCESS_KEY_ID: str = Field(default="", description="Access key for S3/MinIO")
    S3_SECRET_ACCESS_KEY: str = Field(default="", description="Secret key for S3/MinIO")
    S3_ENDPOINT_URL: str = Field(
        default="http://localhost:9000",
        description="Endpoint URL (e.g., http://localhost:9000 for MinIO)",
    )
    S3_REGION_NAME: str = Field(default="eu-west-3", description="S3 region name")

    @property
    def DB_BASE(self):
        return self.DB_NAME

    @property
    def DB_URL(self) -> PostgresDsn:
        """
        Assemble Database URL from settings.

        :return: Database URL.
        """

        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_BASE}"


class TestSettings(Settings):
    @property
    def DB_BASE(self):
        return f"{self.DB_NAME}_test"


settings = TestSettings() if "pytest" in modules else Settings()
