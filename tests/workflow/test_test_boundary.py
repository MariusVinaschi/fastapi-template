import pytest

from scripts.environment import apply_test_environment
from scripts.workflow import ROOT


@pytest.mark.anyio
@pytest.mark.unit
async def test_unit_cannot_request_database_fixture_dynamically(request):
    shared_fixtures = request.config.pluginmanager.get_plugin(str(ROOT / "conftest.py"))
    assert shared_fixtures is not None
    generator = shared_fixtures.db_session.__wrapped__(request)
    with pytest.raises(pytest.fail.Exception, match="Unit tests cannot request db_session"):
        await anext(generator)


def test_test_environment_removes_export_token():
    env = {"LOGFIRE_TOKEN": "example", "APP_DB_NAME": "application", "APP_DB_TEST_NAME": "application_test"}
    apply_test_environment(env)
    assert env["LOGFIRE_TOKEN"] == ""
    assert env["LOGFIRE_SEND_TO_LOGFIRE"] == "false"
    assert env["APP_DB_NAME"] == "application_test"
