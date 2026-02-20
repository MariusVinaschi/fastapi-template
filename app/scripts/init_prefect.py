import asyncio
import json
import os
from pathlib import Path

from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolCreate
from prefect_sqlalchemy import AsyncDriver, ConnectionComponents, SqlAlchemyConnector


def build_db_connector() -> SqlAlchemyConnector:
    """Construct the SQLAlchemyConnector block with connection URI."""
    return SqlAlchemyConnector(
        connection_info=ConnectionComponents(
            driver=AsyncDriver.POSTGRESQL_ASYNCPG,
            username=os.getenv("APP_DB_USER", "fastapitemplateuser"),
            password=os.getenv("APP_DB_PASSWORD", "fastapitemplatepassword"),
            host=os.getenv("APP_DB_HOST", "dbapp"),
            port=os.getenv("APP_DB_PORT", 5432),
            database=os.getenv("APP_DB_NAME", "fastapitemplatedb"),
        )
    )


async def save_block(block, slug):
    """Persist the block and provide a short confirmation."""
    await block.save(slug, overwrite=True)
    print(f"Saved Prefect block '{slug}'")


def _split_env_list(var_name: str, default_value: str) -> list[str]:
    """Return a clean list from comma-separated environment variables."""
    raw_value = os.getenv(var_name, default_value)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def load_work_pool_template() -> dict:
    """Load and customize the Docker work-pool template."""
    template_path = Path(__file__).with_name("work_pool_template.json")
    template = json.loads(template_path.read_text())

    image_override = os.getenv("WORK_POOL_IMAGE")
    if image_override:
        template.setdefault("variables", {}).setdefault("properties", {}).setdefault("image", {})["default"] = (
            image_override
        )

    networks_override = _split_env_list("WORK_POOL_NETWORKS", "prefect_network,app_network")
    if networks_override:
        template.setdefault("variables", {}).setdefault("properties", {}).setdefault("networks", {})["default"] = (
            networks_override
        )

    # Set auto_remove to True by default
    template.setdefault("variables", {}).setdefault("properties", {}).setdefault("auto_remove", {})["default"] = True

    return template


async def ensure_work_pool():
    """Create or update the Docker work pool using the JSON template."""
    name = os.getenv("WORK_POOL_NAME", "my-docker-pool")
    description = os.getenv("WORK_POOL_DESCRIPTION", "My Docker Pool")
    base_job_template = load_work_pool_template()

    async with get_client() as client:
        work_pool = WorkPoolCreate(
            name=name,
            type="docker",
            description=description,
            base_job_template=base_job_template,
        )
        await client.create_work_pool(work_pool, overwrite=True)
        print(f"Ensured Prefect work pool '{name}' exists/updated.")


async def main():
    block_slug = os.getenv("PREFECT_BLOCK_NAME_SQLALCHEMY", "dbapp-sqlalchemy")
    await save_block(build_db_connector(), block_slug)
    await ensure_work_pool()


def cli():
    """Entry point for the console script"""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
