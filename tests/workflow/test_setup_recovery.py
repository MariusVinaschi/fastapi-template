import subprocess

import pytest

from scripts import workflow
from scripts.environment import ENV_FILE, worktree_env


@pytest.fixture
def isolated_setup(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("PRESERVED_SETTING=keep-me\n")
    monkeypatch.setattr(workflow, "ensure_server", lambda _: None)
    monkeypatch.setattr(workflow, "provision", lambda *args, **kwargs: None)
    return tmp_path


def test_failed_migration_can_resume_without_replacing_identity_or_environment(isolated_setup, monkeypatch):
    migrations = []

    def migrate(command, **kwargs):
        migrations.append(command)
        if len(migrations) == 1:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(workflow.subprocess, "run", migrate)

    with pytest.raises(subprocess.CalledProcessError):
        workflow.setup(isolated_setup)
    interrupted = worktree_env(isolated_setup)
    assert "WORKTREE_READY" not in interrupted

    workflow.setup(isolated_setup)
    recovered = worktree_env(isolated_setup)
    assert recovered == {**interrupted, "WORKTREE_READY": "1"}
    assert (isolated_setup / ".env").read_text() == "PRESERVED_SETTING=keep-me\n"


def test_cleanup_removes_the_generated_environment_and_is_repeatable(isolated_setup, monkeypatch):
    monkeypatch.setattr(workflow.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 0))
    workflow.setup(isolated_setup)
    assert workflow.cleanup(isolated_setup) == 0
    assert not (isolated_setup / ENV_FILE).exists()
    assert workflow.cleanup(isolated_setup) == 0


def test_status_reports_missing_environment_without_guessing(tmp_path):
    assert workflow.status(tmp_path) == 1
