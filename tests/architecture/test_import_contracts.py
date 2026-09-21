"""Each import contract, proven against a violation and against the real tree.

A contract that matches nothing is indistinguishable from a satisfied contract, so
every contract shipped in `pyproject.toml` has a fixture package here that it must
reject (AC-09). The real tree is then checked against the shipped configuration.
"""

import tomllib

import pytest

from tests.architecture.conftest import REPO_ROOT, run_lint_imports

pytestmark = pytest.mark.architecture


def _config(root_package: str, contract: str) -> str:
    return f"[importlinter]\nroot_package = {root_package}\ninclude_external_packages = True\n\n{contract}"


FRAMEWORK_FREE = _config(
    "frameworkleak",
    """[importlinter:contract:c]
name = Domains are framework-agnostic
type = forbidden
source_modules =
    frameworkleak.domains
forbidden_modules =
    fastapi
    starlette
    prefect
""",
)

WORKERS_WITHOUT_API = _config(
    "workerleak",
    """[importlinter:contract:c]
name = Workers never import the HTTP API
type = forbidden
source_modules =
    workerleak.workers
forbidden_modules =
    workerleak.api
""",
)

LAYERS = _config(
    "layerbreak",
    """[importlinter:contract:c]
name = Application layers
type = layers
layers =
    layerbreak.api
    layerbreak.domains
    layerbreak.infrastructure
""",
)

PRIVATE_REPOSITORY = _config(
    "repoleak",
    """[importlinter:contract:c]
name = The alpha repository is private to its domain
type = protected
protected_modules =
    repoleak.domains.alpha.repository
allowed_importers =
    repoleak.domains.alpha
""",
)


@pytest.mark.parametrize(
    ("fixture", "config", "contract", "offender"),
    [
        pytest.param(
            "frameworkleak",
            FRAMEWORK_FREE,
            "Domains are framework-agnostic",
            "frameworkleak.domains.thing",
            id="AC-A1-domain-imports-a-framework",
        ),
        pytest.param(
            "workerleak",
            WORKERS_WITHOUT_API,
            "Workers never import the HTTP API",
            "workerleak.workers.job",
            id="AC-A2-worker-imports-the-api",
        ),
        pytest.param(
            "layerbreak",
            LAYERS,
            "Application layers",
            "layerbreak.infrastructure.settings",
            id="AC-A3-lower-layer-imports-higher",
        ),
        pytest.param(
            "repoleak",
            PRIVATE_REPOSITORY,
            "The alpha repository is private to its domain",
            "repoleak.domains.beta.service",
            id="AC-A4-cross-domain-repository-import",
        ),
    ],
)
def test_a_violation_breaks_its_contract(violating_tree, fixture, config, contract, offender):
    result = violating_tree(fixture, config)

    assert not result.is_clean, f"{contract} accepted a deliberate violation"
    assert result.broke(contract)
    assert offender in result.output, "the failure must name the offending module"


def test_the_real_tree_satisfies_every_contract():
    """AC-A1 to AC-A6: the shipped configuration holds on app/."""
    result = run_lint_imports(REPO_ROOT / "pyproject.toml", REPO_ROOT)

    assert result.is_clean, result.output


def test_every_domain_confines_its_repository():
    """AC-A5: a new domain cannot arrive without its own confinement contract.

    The wildcard form of this contract is worse than none: with every domain in the
    allow-list, a real cross-domain import reports KEPT.
    """
    contracts = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["tool"]["importlinter"]["contracts"]
    protected = {m for c in contracts if c["type"] == "protected" for m in c["protected_modules"]}

    domains = {p.parent.name for p in (REPO_ROOT / "app" / "domains").glob("*/repository.py")} - {"base"}
    assert domains, "no domain repository found — the discovery itself is broken"

    missing = {d for d in domains if f"app.domains.{d}.repository" not in protected}
    assert not missing, f"domains without a confinement contract: {sorted(missing)}"

    assert not any("*" in m for m in protected), "wildcards make this contract silently permissive"


def test_no_infrastructure_module_imports_a_domain():
    """AC-A6: the auth adapter left infrastructure, and nothing took its place."""
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{n}"
        for path in (REPO_ROOT / "app" / "infrastructure").rglob("*.py")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if line.startswith(("from app.domains", "import app.domains"))
    ]

    assert not offenders, f"infrastructure must sit below the domains: {offenders}"
