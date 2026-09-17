"""CLI behind just setup, cleanup and status. Every other recipe is plain shell."""

import argparse
import secrets
import subprocess
import sys
from pathlib import Path

from scripts.databases import ensure_server, provision
from scripts.environment import (
    DEV_DB_PORT,
    ENV_FILE,
    choose_port,
    database_names,
    identity,
    runtime_environment,
    worktree_env,
    write_env,
)

ROOT = Path(__file__).resolve().parents[1]


def generated_environment(root: Path) -> dict[str, str]:
    worktree_id = identity(root)
    app_name, test_name = database_names(worktree_id)
    return {
        "WORKTREE_ID": worktree_id,
        "WORKTREE_ROOT": str(root.resolve()),
        "WORKTREE_TOKEN": secrets.token_hex(24),
        "APP_PORT": str(choose_port(root)),
        "APP_DB_HOST": "127.0.0.1",
        "APP_DB_PORT": DEV_DB_PORT,
        "APP_DB_NAME": app_name,
        "APP_DB_TEST_NAME": test_name,
        "SECRET_KEY": secrets.token_urlsafe(32),
        "LOGFIRE_SEND_TO_LOGFIRE": "false",
    }


def database_user(env: dict[str, str]) -> str:
    return env.get("APP_DB_USER", "fastapitemplateuser")


def setup(root: Path) -> int:
    # Environment files are bootstrapped by the env-init recipe setup depends on.
    values = worktree_env(root) or generated_environment(root)
    # Readiness is cleared first so an interrupted setup cannot look complete.
    values.pop("WORKTREE_READY", None)
    write_env(root / ENV_FILE, values)
    ensure_server(root)
    env = runtime_environment(root)
    provision(database_user(env), database_names(values["WORKTREE_ID"]), values["WORKTREE_TOKEN"])
    subprocess.run(["uv", "run", "--locked", "alembic", "upgrade", "head"], cwd=root, env=env, check=True)
    write_env(root / ENV_FILE, {**values, "WORKTREE_READY": "1"})
    print(f"Ready: {values['WORKTREE_ID']} — http://127.0.0.1:{values['APP_PORT']}")
    return 0


def cleanup(root: Path) -> int:
    values = worktree_env(root)
    if not values:
        print("No managed environment to clean up")
        return 0
    env = runtime_environment(root)
    names = database_names(values["WORKTREE_ID"])
    provision(database_user(env), names, values["WORKTREE_TOKEN"], drop=True)
    (root / ENV_FILE).unlink()
    print(f"Dropped {names[0]} and {names[1]}; the shared development container is retained")
    return 0


def status(root: Path) -> int:
    values = worktree_env(root)
    if not values:
        print("No managed environment — run just setup")
        return 1
    ready = values.get("WORKTREE_READY") == "1"
    print(f"id={values['WORKTREE_ID']} port={values['APP_PORT']} ready={ready}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "cleanup", "status"])
    args = parser.parse_args()
    try:
        return {"setup": setup, "cleanup": cleanup, "status": status}[args.command](ROOT)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Workflow error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
