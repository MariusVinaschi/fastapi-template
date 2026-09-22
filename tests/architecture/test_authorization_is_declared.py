"""AC-B6: every domain declares its authorization, and its repository wires it.

Only runtime introspection can decide "wires": it instantiates each domain
repository (a session placeholder is enough -- `__init__` only stores it) and
inspects the resulting `scope_strategy`, which is set by composition, not by any
inspectable literal in source.
"""

import importlib
import inspect
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.domains.base.authorization import AuthorizationScopeStrategy
from app.domains.base.repository import BaseRepository

pytestmark = pytest.mark.architecture

REPO_ROOT = Path(__file__).resolve().parents[2]


def _has_repository_module(domain_dir: Path) -> bool:
    """A repository is a module either way Python accepts it as one."""
    return (domain_dir / "repository.py").exists() or (domain_dir / "repository" / "__init__.py").exists()


def _all_domains() -> set[str]:
    return {
        entry.name
        for entry in (REPO_ROOT / "app" / "domains").iterdir()
        if entry.is_dir() and entry.name != "base" and not entry.name.startswith("__")
    }


# A domain filtered out here because it lacks a *.py-named repository would silently
# never be parametrized below -- pytest turns an empty parametrize list into a skip,
# not a failure. test_every_domain_has_a_discovered_repository is what actually
# guards against that; this list itself must never be trusted to be complete.
DOMAINS = sorted(d for d in _all_domains() if _has_repository_module(REPO_ROOT / "app" / "domains" / d))


def _repository_classes(domain: str) -> Iterator[type]:
    module = importlib.import_module(f"app.domains.{domain}.repository")
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if issubclass(cls, BaseRepository) and cls.__module__ == module.__name__:
            yield cls


def _wired_strategy(repository_cls: type) -> AuthorizationScopeStrategy | None:
    """Build the repository with a placeholder session and read what it wired.

    `BaseRepository.__init__` performs no I/O -- it only assigns its arguments -- so
    a bare `object()` is a safe stand-in for a real session and no database is
    required (AC-04).
    """
    instance = repository_cls(session=object())
    strategy = getattr(instance, "scope_strategy", None)
    return strategy if isinstance(strategy, AuthorizationScopeStrategy) else None


def test_every_domain_has_a_discovered_repository():
    """AC-09: an empty or partial DOMAINS list would silently skip, not fail, below."""
    all_domains = _all_domains()
    assert all_domains, "no domain directory found -- discovery itself is broken"
    assert set(DOMAINS) == all_domains, f"domains with no discovered repository module: {all_domains - set(DOMAINS)}"


@pytest.mark.parametrize("domain", DOMAINS)
def test_every_repository_wires_a_scope_strategy_from_its_own_domain(domain):
    classes = list(_repository_classes(domain))
    assert classes, f"{domain} has no repository class to check"

    for repository_cls in classes:
        strategy = _wired_strategy(repository_cls)
        assert strategy is not None, f"{repository_cls.__qualname__} wires no AuthorizationScopeStrategy"
        assert strategy.__class__.__module__ == f"app.domains.{domain}.authorization", (
            f"{repository_cls.__qualname__} wires {strategy.__class__.__module__}."
            f"{strategy.__class__.__name__}, not a strategy from its own domain"
        )


def test_a_repository_without_a_strategy_is_caught():
    """AC-09: prove the sensor can fail, on a fixture repository, not the real ones."""

    class NoStrategyRepository(BaseRepository):
        def __init__(self, session, authorization_context=None):
            self.session = session
            self.authorization_context = authorization_context
            # deliberately never sets self.scope_strategy

    assert _wired_strategy(NoStrategyRepository) is None
