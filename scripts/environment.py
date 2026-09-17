"""Worktree identity, its generated environment file and its API port."""

import hashlib
import os
import re
import socket
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = ".env.worktree"
PORTS = range(18000, 19000)
DEV_DB_PORT = "5433"


def identity(root: Path) -> str:
    digest = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "_", root.name.lower()).strip("_")[:20] or "worktree"
    return f"wt_{slug}_{digest}"


def database_names(worktree_id: str) -> tuple[str, str]:
    return f"{worktree_id}_app", f"{worktree_id}_test"


def port_available(port: int) -> bool:
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def choose_port(root: Path) -> int:
    """Derived from the checkout path, so distinct worktrees start from distinct ports."""
    start = int(hashlib.sha256(str(root.resolve()).encode()).hexdigest(), 16) % len(PORTS)
    for offset in range(len(PORTS)):
        port = PORTS[(start + offset) % len(PORTS)]
        if port_available(port):
            return port
    raise ValueError(f"No available API port in {PORTS.start}..{PORTS.stop - 1}")


def write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f"{path.name}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(text)
    temporary.replace(path)


def write_env(path: Path, values: dict[str, str]) -> None:
    write_private(path, "".join(f"{key}={value}\n" for key, value in values.items()))


def worktree_env(root: Path) -> dict[str, str]:
    """This checkout's generated values; empty before setup."""
    values = {key: value for key, value in dotenv_values(root / ENV_FILE).items() if value is not None}
    if values and values.get("WORKTREE_ROOT") != str(root.resolve()):
        raise ValueError(f"{ENV_FILE} was generated for another checkout; run just setup again")
    return values


def runtime_environment(root: Path, *, testing: bool = False) -> dict[str, str]:
    values = {
        **dotenv_values(root / ".env"),
        **dotenv_values(root / ".env.local"),
        **worktree_env(root),
        **os.environ,
    }
    env = {key: value for key, value in values.items() if value is not None}
    if testing:
        apply_test_environment(env)
    return env


def apply_test_environment(env: dict[str, str]) -> None:
    test_name = env.get("APP_DB_TEST_NAME", "fastapi_template_test").lstrip("/")
    if not test_name or test_name in {"postgres", "template0", "template1"}:
        raise ValueError("Invalid test database name")
    if not env.get("WORKFLOW_TESTING") and not os.environ.get("CI") and test_name == env.get("APP_DB_NAME"):
        raise ValueError("Test database must differ from the application database")
    env.update(
        APP_DB_NAME=test_name,
        APP_DB_TEST_NAME=test_name,
        LOGFIRE_SEND_TO_LOGFIRE="false",
        LOGFIRE_TOKEN="",
        WORKFLOW_TESTING="1",
    )
    env.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
