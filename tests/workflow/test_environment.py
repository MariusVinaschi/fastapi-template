import pytest

from scripts.environment import (
    ENV_FILE,
    PORTS,
    UNPROVISIONED,
    apply_test_environment,
    choose_port,
    database_names,
    identity,
    runtime_environment,
    worktree_env,
    write_env,
)


@pytest.fixture
def managed(tmp_path, monkeypatch):
    """A complete generated file, with no ambient database variables."""
    for key in ("APP_DB_HOST", "APP_DB_PORT", "APP_DB_NAME", "APP_DB_TEST_NAME", "APP_DB_USER", UNPROVISIONED):
        monkeypatch.delenv(key, raising=False)
    write_env(
        tmp_path / ENV_FILE,
        {
            "WORKTREE_ROOT": str(tmp_path.resolve()),
            "APP_DB_HOST": "127.0.0.1",
            "APP_DB_PORT": "5433",
            "APP_DB_NAME": "wt_example_app",
            "APP_DB_TEST_NAME": "wt_example_test",
        },
    )
    return tmp_path


def test_identity_is_stable_and_distinguishes_same_named_directories(tmp_path):
    first = tmp_path / "a" / "feature"
    second = tmp_path / "b" / "feature"
    assert identity(first) == identity(first)
    assert identity(first) != identity(second)
    assert len(identity(first)) < 50


def test_database_names_derive_from_identity():
    assert database_names("wt_x_0123456789ab") == ("wt_x_0123456789ab_app", "wt_x_0123456789ab_test")


def test_environment_file_round_trip_and_private_permissions(tmp_path):
    values = {"WORKTREE_ROOT": str(tmp_path.resolve()), "APP_PORT": "18500"}
    write_env(tmp_path / ENV_FILE, values)
    assert worktree_env(tmp_path) == values
    assert (tmp_path / ENV_FILE).stat().st_mode & 0o777 == 0o600


def test_environment_file_from_another_checkout_is_refused(tmp_path):
    write_env(tmp_path / ENV_FILE, {"WORKTREE_ROOT": str(tmp_path / "elsewhere")})
    with pytest.raises(ValueError, match="another checkout"):
        worktree_env(tmp_path)


def test_missing_environment_file_is_explicitly_empty(tmp_path):
    assert worktree_env(tmp_path) == {}


def test_generated_values_override_the_committed_configuration(managed):
    (managed / ".env").write_text("APP_DB_NAME=committed\nAPP_DB_USER=shared\n")
    env = runtime_environment(managed)
    assert env["APP_DB_NAME"] == "wt_example_app"
    assert env["APP_DB_USER"] == "shared"


@pytest.mark.parametrize("key", ["APP_DB_HOST", "APP_DB_PORT", "APP_DB_NAME", "APP_DB_TEST_NAME"])
def test_ambient_variable_cannot_move_a_managed_database(managed, monkeypatch, key):
    monkeypatch.setenv(key, "somewhere-else")
    with pytest.raises(ValueError, match=f"{key} is owned by"):
        runtime_environment(managed, testing=True)


def test_matching_ambient_variable_is_accepted(managed, monkeypatch):
    monkeypatch.setenv("APP_DB_TEST_NAME", "wt_example_test")
    assert runtime_environment(managed, testing=True)["APP_DB_NAME"] == "wt_example_test"


def test_incomplete_generated_file_is_refused(tmp_path, monkeypatch):
    monkeypatch.delenv(UNPROVISIONED, raising=False)
    write_env(tmp_path / ENV_FILE, {"WORKTREE_ROOT": str(tmp_path.resolve()), "APP_DB_HOST": "127.0.0.1"})
    with pytest.raises(ValueError, match="lacks"):
        runtime_environment(tmp_path)


def test_generated_file_naming_one_database_twice_is_refused(tmp_path, monkeypatch):
    monkeypatch.delenv(UNPROVISIONED, raising=False)
    write_env(
        tmp_path / ENV_FILE,
        {
            "WORKTREE_ROOT": str(tmp_path.resolve()),
            "APP_DB_HOST": "127.0.0.1",
            "APP_DB_PORT": "5433",
            "APP_DB_NAME": "same",
            "APP_DB_TEST_NAME": "same",
        },
    )
    with pytest.raises(ValueError, match="two different databases"):
        runtime_environment(tmp_path)


@pytest.mark.parametrize("value", ["false", "0", "", "yes"])
def test_unprovisioned_consent_needs_an_exact_opt_in(tmp_path, monkeypatch, value):
    # A non-empty value such as "false" used to pass a truthiness check.
    monkeypatch.setenv(UNPROVISIONED, value)
    with pytest.raises(ValueError, match="run just setup"):
        runtime_environment(tmp_path, testing=True)


def test_unprovisioned_consent_requires_complete_coordinates(tmp_path, monkeypatch):
    monkeypatch.setenv(UNPROVISIONED, "1")
    monkeypatch.delenv("APP_DB_TEST_NAME", raising=False)
    with pytest.raises(ValueError, match="requires explicit"):
        runtime_environment(tmp_path, testing=True)


@pytest.mark.parametrize("name", ["postgres", "template1", "Mixed_Case", "has-dash", "x" * 64])
def test_protected_or_malformed_test_database_is_refused(name):
    with pytest.raises(ValueError, match="Refusing to create and drop tables"):
        apply_test_environment({"APP_DB_TEST_NAME": name})


def test_port_is_stable_per_checkout_and_differs_between_checkouts(tmp_path):
    first = tmp_path / "a" / "feature"
    second = tmp_path / "b" / "feature"
    assert choose_port(first) == choose_port(first)
    assert choose_port(first) != choose_port(second)
    assert choose_port(first) in PORTS


def test_occupied_port_is_skipped(tmp_path, monkeypatch):
    taken = choose_port(tmp_path)
    monkeypatch.setattr("scripts.environment.port_available", lambda port: port != taken)
    assert choose_port(tmp_path) != taken
