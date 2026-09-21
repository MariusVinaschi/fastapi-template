"""Create and drop only the databases this checkout owns, inside the project's own container."""

import re
import subprocess
from pathlib import Path

COMPOSE_FILE = "docker-compose.dev.yml"
CONTAINER = "fastapi-template-dev-db"
UNMARKED = "<unmarked>"
SAFE_NAME = re.compile(r"wt_[a-z0-9_]{1,50}")
SAFE_TOKEN = re.compile(r"[0-9a-f]{16,64}")


def ensure_server(root: Path) -> None:
    """The development server is this project's container, never whatever happens to listen."""
    subprocess.run(
        ["docker", "compose", "-f", str(root / COMPOSE_FILE), "up", "-d", "--wait", "--wait-timeout", "60"],
        cwd=root,
        check=True,
    )


def psql(user: str, sql: str) -> str:
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "psql", "-U", user, "-d", "postgres", "-tAc", sql],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"Development PostgreSQL rejected the statement: {result.stderr.strip()}")
    return result.stdout.strip()


def checked(value: str, pattern: re.Pattern[str], kind: str) -> str:
    # Identifiers are interpolated into SQL, so only generated shapes are accepted.
    if not pattern.fullmatch(value):
        raise ValueError(f"Refusing to use an unexpected {kind}: {value!r}")
    return value


def current_owner(user: str, name: str) -> str | None:
    """None when the database is absent; UNMARKED when it exists without a token."""
    found = psql(
        user,
        f"SELECT coalesce(shobj_description(oid, 'pg_database'), '{UNMARKED}') "
        f"FROM pg_database WHERE datname = '{name}'",
    )
    return found or None


def manage(user: str, name: str, token: str, *, drop: bool) -> None:
    checked(name, SAFE_NAME, "database name")
    checked(token, SAFE_TOKEN, "ownership token")
    owner = current_owner(user, name)
    if owner is not None and owner != token:
        raise ValueError(f"Database {name} exists without this checkout's ownership token")
    if drop and owner is not None:
        psql(user, f'DROP DATABASE "{name}"')
    elif not drop and owner is None:
        psql(user, f'CREATE DATABASE "{name}"')
        psql(user, f"COMMENT ON DATABASE \"{name}\" IS '{token}'")


def provision(user: str, names: tuple[str, str], token: str, *, drop: bool = False) -> None:
    for name in names:
        manage(user, name, token, drop=drop)
