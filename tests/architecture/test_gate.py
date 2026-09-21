"""The gate is reachable, self-contained, and identical locally and in CI."""

import os
import re
import subprocess
import sys

import pytest

from tests.architecture.conftest import REPO_ROOT

pytestmark = pytest.mark.architecture

RECIPE = "architecture-check"


def _justfile() -> str:
    return (REPO_ROOT / "Justfile").read_text()


def _recipe_body(name: str) -> str:
    """The lines of a just recipe, up to the next top-level definition."""
    match = re.search(rf"^{re.escape(name)}:(?P<deps>.*)$(?P<body>(\n(?:[ \t]+.*)?)*)", _justfile(), re.MULTILINE)
    assert match, f"no `{name}` recipe in the Justfile"
    return match.group("deps") + match.group("body")


def test_a_dedicated_recipe_runs_the_architecture_gate():
    """AC-08: the checks are runnable on their own."""
    body = _recipe_body(RECIPE)

    assert "lint-imports" in body, "the import contracts must run in the dedicated recipe"
    assert "tests/architecture" in body, "the architecture tests must run in the dedicated recipe"


def test_the_full_check_cannot_pass_while_the_gate_fails():
    """AC-08: `just check` contains the dedicated recipe."""
    assert RECIPE in _recipe_body("check")


def test_ci_runs_the_same_recipe():
    """AC-03: one entry point, so CI and a developer cannot disagree."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()

    assert f"just {RECIPE}" in workflow, "CI must invoke the same recipe, not a restated rule list"


def test_the_git_hook_runs_the_same_recipe():
    """AC-03: the hook cannot drift from the recipe either."""
    assert RECIPE in (REPO_ROOT / "prek.toml").read_text()


@pytest.mark.skipif(
    os.environ.get("ARCHITECTURE_GATE_NESTED") == "1",
    reason="this test re-runs the suite; the inner run must not recurse",
)
def test_the_gate_needs_no_database():
    """AC-04: the checks run against source and in-process types only."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/architecture",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "tests.architecture.no_network",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        # The outer run already rewrote the database coordinates for testing; passing
        # them down would look like ambient values overriding .env.worktree, which the
        # environment guard rightly refuses. Let the child derive its own.
        env={k: v for k, v in os.environ.items() if not k.startswith("APP_DB_")} | {"ARCHITECTURE_GATE_NESTED": "1"},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
