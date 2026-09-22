"""Every shipped import contract, proven against a violation and against the real tree.

Each contract in `pyproject.toml` is rebased onto a fixture package's root (see
`pyproject_contracts.py`) and run there -- not reconstructed by hand. A hand-retyped
copy would keep passing after the real contract was deleted or renamed; rebasing the
actual shipped contract cannot (AC-09).
"""

import ast
import tempfile
import tomllib
from pathlib import Path

import pytest

from tests.architecture.lint_imports import REPO_ROOT, run_lint_imports
from tests.architecture.pyproject_contracts import load_contracts, render_ini

pytestmark = pytest.mark.architecture

# contract name -> (fixture package, a module path that must appear in the failure).
# A shipped contract with no entry here fails loudly (test_every_contract_is_registered
# and the fixture below), rather than being silently unproven.
FIXTURES = {
    "Domains are framework-agnostic": ("frameworkleak", "frameworkleak.domains.thing"),
    "Workers never import the HTTP API": ("workerleak", "workerleak.workers.job"),
    "Application layers": ("layerbreak", "layerbreak.infrastructure.settings"),
    "The users repository is private to its domain": ("repoleak", "repoleak.domains.sessions.service"),
    "The sessions repository is private to its domain": ("repoleak", "repoleak.domains.users.service"),
}


def _shipped_contracts() -> list[dict]:
    return load_contracts(REPO_ROOT / "pyproject.toml")


def test_every_shipped_contract_is_registered_for_proof():
    """AC-09: a contract with no fixture is unproven, not merely untested by name."""
    shipped = {c["name"] for c in _shipped_contracts()}
    assert shipped, "no contracts found in pyproject.toml -- discovery itself is broken"
    unregistered = shipped - FIXTURES.keys()
    assert not unregistered, f"shipped contracts with no registered fixture: {unregistered}"
    orphaned = FIXTURES.keys() - shipped
    assert not orphaned, f"registered fixtures for contracts no longer shipped: {orphaned}"


@pytest.mark.parametrize("contract", _shipped_contracts(), ids=lambda c: c["name"])
def test_a_shipped_contract_breaks_on_its_registered_violation(contract, violating_tree):
    fixture, offender = FIXTURES[contract["name"]]
    config = render_ini(contract, fixture_root=fixture)

    result = violating_tree(fixture, config)

    assert not result.is_clean, f"{contract['name']} accepted a deliberate violation:\n{config}"
    assert result.broke(contract["name"])
    assert offender in result.output, "the failure must name the offending module"


def test_the_real_tree_satisfies_every_shipped_contract():
    """AC-A1 to AC-A6: the shipped configuration holds on app/, unmodified."""
    result = run_lint_imports(REPO_ROOT / "pyproject.toml", REPO_ROOT)
    assert result.is_clean, result.output


def test_every_domain_confines_its_repository():
    """AC-A5: a new domain cannot arrive without its own confinement contract.

    The wildcard form of this contract is worse than none: with every domain in the
    allow-list, a real cross-domain import reports KEPT (measured before writing
    this test).
    """
    protected = {
        c["protected_modules"][0]: c["allowed_importers"] for c in _shipped_contracts() if c["type"] == "protected"
    }

    domain_dirs = [
        p
        for p in (REPO_ROOT / "app" / "domains").iterdir()
        if p.is_dir() and p.name != "base" and not p.name.startswith("__")
    ]
    assert domain_dirs, "no domain directory found -- discovery itself is broken"

    for domain in domain_dirs:
        has_repository = (domain / "repository.py").exists() or (domain / "repository" / "__init__.py").exists()
        if not has_repository:
            continue
        expected_module = f"app.domains.{domain.name}.repository"
        assert expected_module in protected, f"{domain.name} has no confinement contract"
        allowed = protected[expected_module]
        assert allowed == [f"app.domains.{domain.name}"], (
            f"{domain.name}'s confinement contract grants {allowed}, wider than its own domain"
        )

    assert not any("*" in module for module in protected), "wildcards make this contract silently permissive"
    assert not any("*" in a for allowed in protected.values() for a in allowed), (
        "a wildcard allowed_importers makes this contract silently permissive"
    )


def test_every_domain_is_placed_in_the_layers_contract():
    """AC-A3/AC-A5: a new domain unlisted in the layers contract is unconstrained
    in both import directions, not merely unconfined at the repository level."""
    layers_contracts = [c for c in _shipped_contracts() if c["type"] == "layers"]
    assert layers_contracts, "no layers contract found -- discovery itself is broken"
    layered_text = "\n".join(" ".join(c["layers"]) for c in layers_contracts)

    domain_dirs = {
        p.name
        for p in (REPO_ROOT / "app" / "domains").iterdir()
        if p.is_dir() and p.name != "base" and not p.name.startswith("__")
    }
    missing = {d for d in domain_dirs if f"app.domains.{d}" not in layered_text}
    assert not missing, f"domains absent from the layers contract: {missing}"


def _domain_import_lines(node: ast.AST) -> list[int]:
    if isinstance(node, ast.ImportFrom):
        return [node.lineno] if node.module and node.module.startswith("app.domains") else []
    if isinstance(node, ast.Import):
        return [node.lineno for alias in node.names if alias.name.startswith("app.domains")]
    return []


def test_no_infrastructure_module_imports_a_domain():
    """AC-A6: the auth adapter left infrastructure, and nothing took its place.

    A source scan, not a substitute for the layers contract (which already covers
    this direction): it exists to give this specific invariant a failure message of
    its own, so it is written to catch the shapes a plain `startswith` misses --
    indented imports, `TYPE_CHECKING` blocks, `from app import domains`.
    """
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{lineno}"
        for path in (REPO_ROOT / "app" / "infrastructure").rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path)))
        for lineno in _domain_import_lines(node)
    ]

    assert not offenders, f"infrastructure must sit below the domains: {offenders}"


def test_ignore_imports_never_ships_a_wildcard():
    """AC-05: an accepted exemption must name the specific import it suppresses.

    import-linter itself has no mechanism to reject a wildcard `ignore_imports`
    entry -- verified below, it silences an unrelated real violation and reports
    KEPT. The policy is therefore enforced here, structurally, by refusing to ship
    one: this test reads every shipped contract's `ignore_imports` and fails if any
    entry contains a wildcard.
    """
    offenders = [
        (contract["name"], entry)
        for contract in _shipped_contracts()
        for entry in contract.get("ignore_imports", [])
        if "*" in entry
    ]
    assert not offenders, f"wildcard ignore_imports entries (name the exact import instead): {offenders}"


def test_import_linter_does_not_itself_reject_a_blanket_ignore(violating_tree):
    """Documents the fact the test above exists to compensate for.

    If this ever starts failing, a newer import-linter gained its own wildcard-ignore
    protection, and the structural ban above may be safe to relax.
    """
    contract = next(c for c in _shipped_contracts() if c["name"] == "Domains are framework-agnostic")
    config = dict(contract)
    config["ignore_imports"] = ["app.domains.** -> **"]
    ini = render_ini(config, fixture_root="frameworkleak")

    result = violating_tree("frameworkleak", ini)

    assert result.is_clean, "import-linter now rejects a blanket ignore_imports -- see this test's docstring"


def test_a_stale_ignore_import_is_rejected():
    """AC-05: an ignore_imports entry naming an import that no longer exists must fail.

    Relies on `unmatched_ignore_imports_alerting = "error"`, declared explicitly in
    pyproject.toml rather than left to import-linter's default.
    """
    settings = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["tool"]["importlinter"]
    assert settings.get("unmatched_ignore_imports_alerting") == "error", (
        "must be declared explicitly, not left to import-linter's default"
    )

    contract = next(c for c in _shipped_contracts() if c["name"] == "Domains are framework-agnostic")
    config = dict(contract)
    config["ignore_imports"] = ["app.domains.users.service -> nonexistent_package_xyz"]
    ini = render_ini(config, fixture_root="app")  # runs against the real tree: the import never existed

    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / ".importlinter"
        config_path.write_text(ini)
        result = run_lint_imports(config_path, REPO_ROOT)

    assert not result.is_clean, "an ignore_imports entry matching nothing must fail, not silently accumulate"
