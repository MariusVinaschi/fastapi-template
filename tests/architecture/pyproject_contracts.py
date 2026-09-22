"""Derive a runnable import-linter config from the real `pyproject.toml` contracts.

The point: a fixture config that is a separate, hand-retyped copy of the shipped
contracts can drift from them silently -- deleting a real contract leaves the
hand-written copy (and every test built on it) unaffected and green. Rebasing the
*actual* shipped contract onto a fixture package's root proves the shipped
configuration itself, not a stand-in for it.
"""

import re
import tomllib
from pathlib import Path

ContractSpec = dict[str, object]

# `app.domains.users.repository` -> `<fixture_root>.domains.users.repository`. The
# lookbehind requires "app." to start a path segment (string start, or after a
# separator like space/pipe/colon), so it can't misfire inside an unrelated word.
_APP_PREFIX = re.compile(r"(?<![\w.])app\.")


def load_contracts(pyproject_path: Path) -> list[ContractSpec]:
    data = tomllib.loads(pyproject_path.read_text())
    return data["tool"]["importlinter"]["contracts"]


def _rebase(value: object, fixture_root: str) -> object:
    if isinstance(value, str):
        return _APP_PREFIX.sub(f"{fixture_root}.", value)
    if isinstance(value, list):
        return [_rebase(item, fixture_root) for item in value]
    return value


def render_ini(contract: ContractSpec, fixture_root: str) -> str:
    """The single shipped contract, rebased onto `fixture_root`, as a runnable INI."""
    lines = [
        "[importlinter]",
        f"root_package = {fixture_root}",
        "include_external_packages = True",
        "",
        "[importlinter:contract:c]",
    ]
    for key, value in contract.items():
        rebased = _rebase(value, fixture_root)
        if isinstance(rebased, list):
            lines.append(f"{key} =")
            lines.extend(f"    {item}" for item in rebased)
        elif isinstance(rebased, bool):
            lines.append(f"{key} = {str(rebased).lower()}")
        else:
            lines.append(f"{key} = {rebased}")
    return "\n".join(lines) + "\n"
