"""AC-09: an ast-grep rule shipped without test cases passes silently.

Reproduced independently by two reviewers: adding a fifth rule file with no
matching test file still leaves `ast-grep test` reporting "N passed; 0 failed",
exit 0. `ast-grep test` only runs the tests that exist; it has no notion of a rule
that should have some and doesn't.
"""

import pytest
import yaml

from tests.architecture.lint_imports import REPO_ROOT

pytestmark = pytest.mark.architecture

RULES_DIR = REPO_ROOT / "rules" / "architecture"
TESTS_DIR = REPO_ROOT / "rules" / "architecture-tests"


def _rule_ids() -> list[str]:
    return sorted(p.stem for p in RULES_DIR.glob("*.yml"))


@pytest.mark.parametrize("rule_id", _rule_ids())
def test_every_rule_has_a_test_file_with_a_rejecting_case(rule_id):
    test_file = TESTS_DIR / f"{rule_id}-test.yml"
    assert test_file.exists(), f"{rule_id} has no test file at {test_file}"

    cases = yaml.safe_load(test_file.read_text())
    assert cases.get("invalid"), f"{rule_id}'s test file has no `invalid` case -- it could never be proven to fire"
    assert cases.get("valid"), f"{rule_id}'s test file has no `valid` case -- it could always fire"


def test_no_test_file_is_orphaned():
    """A test file for a rule that no longer exists is a dead artifact, not a check."""
    rule_ids = set(_rule_ids())
    orphans = [
        p.stem.removesuffix("-test")
        for p in TESTS_DIR.glob("*-test.yml")
        if p.stem.removesuffix("-test") not in rule_ids
    ]
    assert not orphans, f"test files with no matching rule: {orphans}"
