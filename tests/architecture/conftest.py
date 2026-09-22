"""Shared fixtures for the architecture gate.

Each contract is proven twice: against a fixture package that must break it, and
against the real tree. A contract matching nothing must be indistinguishable from a
broken contract (AC-09), so a fixture that fails to trigger is itself a failure.
"""

import shutil
from pathlib import Path

import pytest

from tests.architecture.lint_imports import REPO_ROOT, LintResult, run_lint_imports

FIXTURES = Path(__file__).parent / "fixtures"

__all__ = ["REPO_ROOT", "LintResult", "run_lint_imports"]  # re-exported for existing importers


@pytest.fixture
def violating_tree(tmp_path: Path):
    """Copy a fixture package into a scratch tree and lint it with a given config."""

    def _build(fixture_name: str, config_body: str) -> LintResult:
        source = FIXTURES / fixture_name
        assert source.is_dir(), f"missing fixture package: {source}"
        shutil.copytree(source, tmp_path / fixture_name, ignore=shutil.ignore_patterns("__pycache__"))
        config = tmp_path / ".importlinter"
        config.write_text(config_body)
        return run_lint_imports(config, tmp_path)

    return _build
