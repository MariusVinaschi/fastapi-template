"""The gate is reachable, self-contained, and identical locally and in CI."""

import os
import re
import subprocess
import sys

import pytest
import yaml

from tests.architecture.lint_imports import REPO_ROOT

pytestmark = pytest.mark.architecture

RECIPE = "architecture-check"
REQUIRED_RECIPE_STEPS = (
    "ast-grep test",
    "ast-grep scan --error=unused-suppression --error=no-suppress-all",
    "lint-imports",
    "tests/architecture",
)


def _justfile() -> str:
    return (REPO_ROOT / "Justfile").read_text()


def _recipe_body(name: str) -> str:
    """The lines of a just recipe, up to the next top-level definition."""
    match = re.search(rf"^{re.escape(name)}:(?P<deps>.*)$(?P<body>(\n(?:[ \t]+.*)?)*)", _justfile(), re.MULTILINE)
    assert match, f"no `{name}` recipe in the Justfile"
    return match.group("deps") + match.group("body")


def test_a_dedicated_recipe_runs_the_architecture_gate():
    """AC-08/AC-09: every check this feature ships actually runs in the recipe.

    Listed by name, not just "lint-imports and tests/architecture": a step can be
    deleted from the recipe without this failing unless each one is named.
    """
    body = _recipe_body(RECIPE)

    for step in REQUIRED_RECIPE_STEPS:
        assert step in body, f"{step!r} must run in the dedicated recipe"
    assert "||" not in body, "a step masked with `||` would not actually fail the gate"


def test_the_full_check_cannot_pass_while_the_gate_fails():
    """AC-08: `just check` contains the dedicated recipe."""
    assert RECIPE in _recipe_body("check")


def test_ci_runs_the_same_recipe():
    """AC-03: one entry point, so CI and a developer cannot disagree.

    Parses the workflow structurally rather than searching its text: a step wrapped
    in `continue-on-error: true` would still contain the string `just
    architecture-check` while never actually failing the job.
    """
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text())

    steps = [step for job in workflow["jobs"].values() for step in job.get("steps", [])]
    matches = [step for step in steps if step.get("run", "").strip() == f"just {RECIPE}"]

    assert matches, "CI must invoke the same recipe, not a restated rule list"
    assert not any(step.get("continue-on-error") for step in matches), (
        "continue-on-error would let the gate fail without failing the job"
    )


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
            "--confcutdir=tests/architecture",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "tests.architecture.no_network",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        # --confcutdir keeps the root conftest.py's database bootstrap out of the
        # child entirely, so no derived environment is needed: the child proves the
        # gate holds with none of this process's env, matching a genuinely
        # unprovisioned checkout rather than one this test happens to run in.
        env={"PATH": os.environ.get("PATH", "")} | {"ARCHITECTURE_GATE_NESTED": "1"},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
