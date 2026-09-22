"""Plain helpers for running import-linter, shared by the architecture tests.

Kept out of conftest.py: importing a conftest module directly
(`from tests.architecture.conftest import ...`) is fragile -- a change to
`__init__.py` layout or import mode can register it twice under two names,
duplicating fixtures. A plain module has no such hazard.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The console script, not `python -m importlinter.cli`: the module form accepts the
# arguments and exits 0 without linting anything, which reads as a clean tree.
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"


@dataclass(frozen=True)
class LintResult:
    exit_code: int
    output: str

    @property
    def is_clean(self) -> bool:
        return self.exit_code == 0

    def broke(self, contract_name: str) -> bool:
        return f"{contract_name} BROKEN" in self.output


def run_lint_imports(config: Path, cwd: Path, *, timeout: float = 60) -> LintResult:
    """Run import-linter with an explicit config, without touching the real one."""
    completed = subprocess.run(
        [str(LINT_IMPORTS), "--config", str(config)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = completed.stdout + completed.stderr
    # A process that produced no output at all analysed nothing -- a broken harness,
    # never a satisfied contract (this is what `python -m importlinter.cli` does: it
    # accepts the arguments and exits 0 silently). A config-level error (e.g. a stale
    # `ignore_imports` entry) legitimately exits before printing "Contracts:", so
    # only emptiness, not that specific string, indicates a dead harness.
    assert output.strip(), "import-linter produced no output at all"
    return LintResult(completed.returncode, output)
