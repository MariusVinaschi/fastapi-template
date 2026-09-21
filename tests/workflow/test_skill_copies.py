from pathlib import Path

import pytest

from scripts.workflow import ROOT

SHARED_SKILLS = ("feature-spec-workflow", "git-workflow", "tdd-implementation")


@pytest.mark.parametrize("name", SHARED_SKILLS)
def test_claude_skill_copy_matches_its_agents_source(name: str):
    source = ROOT / ".agents/skills" / name / "SKILL.md"
    copy = ROOT / ".claude/skills" / name / "SKILL.md"
    assert copy.exists(), f"Missing Claude copy of {name}; copy it from {source}"
    assert copy.read_text() == source.read_text(), f"{name} drifted; .agents/skills is the source"


@pytest.mark.parametrize("name", SHARED_SKILLS)
def test_claude_skill_copy_is_a_regular_file(name: str):
    # Symlinks degrade to plain text on checkouts without symlink support.
    copy: Path = ROOT / ".claude/skills" / name / "SKILL.md"
    assert not copy.is_symlink()
