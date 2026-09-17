import os
import subprocess
import sys

import pytest

from scripts.workflow import ROOT


@pytest.mark.parametrize("binding,step,code", [(False, False, 4), (True, False, 1), (True, True, 0)])
def test_gherkin_execution_requires_bindings_and_steps(tmp_path, binding, step, code):
    features = tmp_path / "features"
    features.mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = features\n")
    (features / "behavior.feature").write_text(
        "Feature: Successful behavior\n  Scenario: an observable result\n    Given a valid input\n",
    )
    source = "def test_placeholder():\n    pass\n"
    if binding:
        source = "from pytest_bdd import scenarios, given\nscenarios('behavior.feature')\n"
    if step:
        source += "@given('a valid input')\ndef valid_input():\n    return True\n"
    (features / "test_behavior.py").write_text(source)
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "pytest_bdd.plugin", "-p", "scripts.pytest_workflow", "-q"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == code, result.stdout + result.stderr
    if step:
        assert "1 passed" in result.stdout


def test_dynamic_database_step_is_selected_as_integration(tmp_path):
    features = tmp_path / "features"
    features.mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = features\n")
    (features / "database.feature").write_text("Feature: Database behavior\n  Scenario: read\n    Given stored data\n")
    (features / "test_database.py").write_text(
        "import pytest\nfrom pytest_bdd import scenarios, given\nscenarios('database.feature')\n"
        "@pytest.fixture\ndef db_session():\n    raise RuntimeError('DB fixture requested')\n"
        "@given('stored data')\ndef data(db_session):\n    pass\n",
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    command = [sys.executable, "-m", "pytest", "-p", "pytest_bdd.plugin", "-p", "scripts.pytest_workflow", "-q"]
    unit = subprocess.run(command + ["-m", "unit"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert unit.returncode == 5 and "1 deselected" in unit.stdout
    integration = subprocess.run(command + ["-m", "integration"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert integration.returncode == 1 and "DB fixture requested" in integration.stdout
