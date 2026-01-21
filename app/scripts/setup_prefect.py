import json
import os
from pathlib import Path

from prefect.blocks.system import Secret
from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolCreate


def build_db_secret():
    """Construct the DB secret payload from environment variables."""
    return Secret(
        name="appdb",
        value={
            "db_host": os.getenv("APP_DB_HOST", "appdb"),
            "db_port": int(os.getenv("APP_DB_PORT", "5432")),
            "db_user": os.getenv("APP_DB_USER", "user"),
            "db_password": os.getenv("APP_DB_PASSWORD", "password"),
            "db_name": os.getenv("APP_DB_NAME", "db"),
        },
    )


def save_block(block, slug):
    """Persist the block and provide a short confirmation."""
    block.save(slug, overwrite=True)
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


def main():
    save_block(build_db_secret(), "appdb")


if __name__ == "__main__":
    main()
