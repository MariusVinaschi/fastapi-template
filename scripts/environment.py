"""Worktree identity, its generated environment file and its API port."""

import hashlib
import os
import re
import socket
import tempfile
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = ".env.worktree"
UNPROVISIONED = "WORKFLOW_ALLOW_UNPROVISIONED_DB"
PORTS = range(18000, 19000)
DEV_DB_PORT = "5433"
# Coordinates a provisioned checkout owns outright: no ambient variable may move them.
OWNED_KEYS = ("APP_DB_HOST", "APP_DB_PORT", "APP_DB_NAME", "APP_DB_TEST_NAME")
PROTECTED_DATABASES = frozenset({"postgres", "template0", "template1"})
SAFE_DATABASE = re.compile(r"[a-z0-9_]{1,63}")


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
    # mkstemp creates a unique file exclusively, so no stale file or symlink is followed.
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_env(path: Path, values: dict[str, str]) -> None:
    write_private(path, "".join(f"{key}={value}\n" for key, value in values.items()))


def worktree_env(root: Path) -> dict[str, str]:
    """This checkout's generated values; empty before setup."""
    values = {key: value for key, value in dotenv_values(root / ENV_FILE).items() if value is not None}
    if values and values.get("WORKTREE_ROOT") != str(root.resolve()):
        raise ValueError(f"{ENV_FILE} was generated for another checkout; run just setup again")
    return values


def runtime_environment(root: Path, *, testing: bool = False) -> dict[str, str]:
    generated = worktree_env(root)
    values = {
        **dotenv_values(root / ".env"),
        **dotenv_values(root / ".env.local"),
        **generated,
        **os.environ,
    }
    env = {key: value for key, value in values.items() if value is not None}
    if generated:
        claim_owned_coordinates(env, generated)
    else:
        require_unprovisioned_consent(env)
    require_distinct_databases(env, provisioned=bool(generated))
    if testing:
        apply_test_environment(env)
    return env


def claim_owned_coordinates(env: dict[str, str], generated: dict[str, str]) -> None:
    """A provisioned checkout never lets an ambient variable move its databases."""
    missing = [key for key in OWNED_KEYS if not generated.get(key)]
    if missing:
        raise ValueError(f"{ENV_FILE} lacks {', '.join(missing)}; run just setup again")
    for key in OWNED_KEYS:
        owned = generated[key]
        ambient = env.get(key)
        if ambient is not None and ambient != owned:
            raise ValueError(f"{key} is owned by {ENV_FILE} ({owned}); refusing ambient value {ambient!r}")
        env[key] = owned


def require_distinct_databases(env: dict[str, str], *, provisioned: bool) -> None:
    """The test database is entirely disposable, so it can never be the application one.

    The test fixture creates and drops every table in whatever APP_DB_TEST_NAME
    names. This holds in both modes and has no override, deliberately: an option
    to allow it would be an option to destroy an application database.
    """
    if env["APP_DB_NAME"] != env["APP_DB_TEST_NAME"]:
        return
    remedy = f"run just setup again to regenerate {ENV_FILE}" if provisioned else "declare two distinct names"
    raise ValueError(
        f"APP_DB_TEST_NAME must differ from APP_DB_NAME (both are {env['APP_DB_NAME']!r}): "
        f"the test suite creates and drops every table in it, and this protection "
        f"has no override — {remedy}"
    )


def require_unprovisioned_consent(env: dict[str, str]) -> None:
    """Nothing was provisioned here, so using a database must be a deliberate, complete choice.

    The test fixture creates and drops tables in whatever it is given, and this
    tooling cannot vouch for a database it did not create.
    """
    if env.get(UNPROVISIONED) != "1":
        raise ValueError(
            f"No {ENV_FILE}: run just setup, or set {UNPROVISIONED}=1 to use a database "
            f"this tooling did not create, with explicit {', '.join(OWNED_KEYS)}"
        )
    missing = [key for key in OWNED_KEYS if not env.get(key)]
    if missing:
        raise ValueError(f"{UNPROVISIONED}=1 requires explicit {', '.join(missing)}")


def apply_test_environment(env: dict[str, str]) -> None:
    test_name = env["APP_DB_TEST_NAME"]
    if test_name in PROTECTED_DATABASES or not SAFE_DATABASE.fullmatch(test_name):
        raise ValueError(f"Refusing to create and drop tables in {test_name!r}")
    env.update(
        APP_DB_NAME=test_name,
        LOGFIRE_SEND_TO_LOGFIRE="false",
        LOGFIRE_TOKEN="",
    )
    env.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
