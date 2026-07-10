"""
Serve Prefect flows from a local process for development.

Equivalent to the deployments in prefect.yaml, but executed in-process: no
Docker image rebuild, no worker. The deployment names match those registered
by prefect.yaml so triggers like `run_deployment("create-user-flow/create-user-flow")`
keep working.

Usage:
    just serve-flows
    # or: uv run serve-flows

Requires PREFECT_API_URL to point at the running Prefect server (from the host,
that is http://localhost:4200/api).
"""

from prefect import serve

from app.workers.flows.web_scrapper import scrape
from app.workers.tasks.database import create_user_flow


def cli() -> None:
    """Entry point for the console script."""
    serve(
        create_user_flow.to_deployment(name="create-user-flow"),
        scrape.to_deployment(name="web-scrapper-flow"),
    )


if __name__ == "__main__":
    cli()
