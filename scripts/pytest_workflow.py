"""Classify collected tests and reject Gherkin contracts without bindings."""

from pathlib import Path

import pytest
from pytest_bdd.parser import FeatureParser


def scenario_key(scenario) -> tuple[str, int]:
    return str(Path(scenario.feature.filename).resolve()), scenario.line_number


def unbound_scenarios(root: Path, items: list[pytest.Item]) -> list[str]:
    bound = {
        scenario_key(item.obj.__scenario__) for item in items if hasattr(getattr(item, "obj", None), "__scenario__")
    }
    missing = []
    for path in sorted((root / "features").rglob("*.feature")):
        feature = FeatureParser(str(path.parent), path.name).parse()
        for scenario in feature.scenarios.values():
            if scenario_key(scenario) not in bound:
                missing.append(f"{path.relative_to(root)}:{scenario.line_number} {scenario.name}")
    return missing


def full_collection(config: pytest.Config) -> bool:
    paths = {str(arg).rstrip("/") for arg in config.args}
    return paths in ({"tests", "features"}, {"features"}, {"."})


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        classify(item)
    if full_collection(config):
        missing = unbound_scenarios(config.rootpath, items)
        if missing:
            raise pytest.UsageError("Unbound Gherkin scenarios:\n" + "\n".join(missing))


def classify(item: pytest.Item) -> None:
    database = "db_session" in getattr(item, "fixturenames", ())
    scenario = hasattr(getattr(item, "obj", None), "__scenario__")
    level = "integration" if database or scenario else "unit"
    if scenario:
        item.add_marker(pytest.mark.bdd)
    marked = item.get_closest_marker("unit") or item.get_closest_marker("integration")
    if not marked:
        item.add_marker(getattr(pytest.mark, level))
    if database and item.get_closest_marker("unit"):
        raise pytest.UsageError(f"Unit test depends on db_session: {item.nodeid}")
