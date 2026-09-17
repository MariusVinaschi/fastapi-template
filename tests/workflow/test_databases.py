import subprocess

import pytest

from scripts import databases
from scripts.databases import CONTAINER, SAFE_NAME, checked, manage, provision
from scripts.environment import database_names, identity


class FakeServer:
    """Records statements and answers ownership lookups like the real container."""

    def __init__(self) -> None:
        self.owners: dict[str, str] = {}
        self.statements: list[str] = []

    def __call__(self, user: str, sql: str) -> str:
        self.statements.append(sql)
        if sql.startswith("SELECT"):
            name = sql.rsplit("'", 2)[1]
            return self.owners.get(name, "")
        name = sql.split('"')[1]
        if sql.startswith("CREATE"):
            self.owners[name] = databases.UNMARKED
        elif sql.startswith("DROP"):
            del self.owners[name]
        else:
            self.owners[name] = sql.rsplit("'", 2)[1]
        return ""


@pytest.fixture
def server(monkeypatch) -> FakeServer:
    fake = FakeServer()
    monkeypatch.setattr(databases, "psql", fake)
    return fake


def test_two_checkouts_own_distinct_databases(tmp_path):
    first = database_names(identity(tmp_path / "a" / "feature"))
    second = database_names(identity(tmp_path / "b" / "feature"))
    assert set(first).isdisjoint(second)


def test_provisioning_is_idempotent_and_removes_only_owned_databases(server):
    names = database_names("wt_example_0123456789ab")
    provision("owner", names, "a" * 48)
    provision("owner", names, "a" * 48)
    assert set(server.owners) == set(names)
    provision("owner", names, "a" * 48, drop=True)
    provision("owner", names, "a" * 48, drop=True)
    assert server.owners == {}


def test_database_without_this_token_is_never_dropped(server):
    server.owners["wt_example_0123456789ab_app"] = "b" * 48
    with pytest.raises(ValueError, match="ownership token"):
        manage("owner", "wt_example_0123456789ab_app", "a" * 48, drop=True)
    assert "wt_example_0123456789ab_app" in server.owners


def test_database_created_without_a_comment_is_rejected_rather_than_adopted(server):
    server.owners["wt_example_0123456789ab_app"] = databases.UNMARKED
    with pytest.raises(ValueError, match="ownership token"):
        manage("owner", "wt_example_0123456789ab_app", "a" * 48, drop=False)


@pytest.mark.parametrize("name", ["postgres", "template1", 'wt_"; DROP DATABASE x; --', "wt_UPPER"])
def test_unexpected_identifiers_never_reach_sql(name):
    with pytest.raises(ValueError, match="unexpected database name"):
        checked(name, SAFE_NAME, "database name")


def container_running() -> bool:
    return subprocess.run(["docker", "exec", CONTAINER, "true"], capture_output=True, check=False).returncode == 0


@pytest.mark.integration
@pytest.mark.skipif(not container_running(), reason="development container is not running")
def test_real_container_round_trip():
    names = database_names("wt_selftest_0123456789ab")
    token = "c" * 48
    provision("fastapitemplateuser", names, token)
    try:
        assert databases.current_owner("fastapitemplateuser", names[0]) == token
    finally:
        provision("fastapitemplateuser", names, token, drop=True)
    assert databases.current_owner("fastapitemplateuser", names[0]) is None
