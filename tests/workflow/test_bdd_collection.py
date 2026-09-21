from types import SimpleNamespace

from pytest_bdd.parser import FeatureParser

from scripts.pytest_workflow import unbound_scenarios


def test_absence_of_gherkin_is_allowed(tmp_path):
    assert unbound_scenarios(tmp_path, []) == []


def test_each_scenario_requires_a_binding(tmp_path):
    directory = tmp_path / "features"
    directory.mkdir()
    path = directory / "behavior.feature"
    path.write_text("Feature: Observable behavior\n  Scenario: first\n    Given a user\n")
    assert "first" in unbound_scenarios(tmp_path, [])[0]
    scenario = FeatureParser(str(directory), path.name).parse().scenarios["first"]
    item = SimpleNamespace(obj=SimpleNamespace(__scenario__=scenario))
    assert unbound_scenarios(tmp_path, [item]) == []
