"""Shared helpers for the architecture gate.

Each contract is proven twice: against a fixture package that must break it, and
against the real tree. A contract matching nothing must be indistinguishable from a
broken contract (AC-09), so a fixture that fails to trigger is itself a failure.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class LintResult:
    exit_code: int
    output: str

    @property
    def is_clean(self) -> bool:
        return self.exit_code == 0

    def broke(self, contract_name: str) -> bool:
        return f"{contract_name} BROKEN" in self.output


# The console script, not `python -m importlinter.cli`: the module form accepts the
# arguments and exits 0 without linting anything, which reads as a clean tree.
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"


def run_lint_imports(config: Path, cwd: Path) -> LintResult:
    """Run import-linter with an explicit config, without touching the real one."""
    completed = subprocess.run(
        [str(LINT_IMPORTS), "--config", str(config)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    # A run that analysed nothing is a broken harness, never a satisfied contract.
    assert "Contracts:" in output, f"import-linter produced no verdict:\n{output}"
    return LintResult(completed.returncode, output)


@pytest.fixture
def violating_tree(tmp_path: Path):
    """Copy a fixture package into a scratch tree and lint it with a given config."""

    def _build(fixture_name: str, config_body: str) -> LintResult:
        source = FIXTURES / fixture_name
        assert source.is_dir(), f"missing fixture package: {source}"
        shutil.copytree(source, tmp_path / fixture_name)
        config = tmp_path / ".importlinter"
        config.write_text(config_body)
        return run_lint_imports(config, tmp_path)

    return _build
